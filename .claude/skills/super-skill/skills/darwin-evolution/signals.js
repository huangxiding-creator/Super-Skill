/**
 * GEP Signals Module for Super-Skill Darwin Evolution
 * Adapted from autogame-17/evolver (MIT License)
 *
 * Signal detection and analysis for protocol-constrained evolution.
 */

// Opportunity signal names (shared with mutation.js and personality.js).
const OPPORTUNITY_SIGNALS = [
  'user_feature_request',
  'user_improvement_suggestion',
  'perf_bottleneck',
  'capability_gap',
  'stable_success_plateau',
  'external_opportunity',
  'recurring_error',
  'unsupported_input_type',
  'evolution_stagnation_detected',
  'repair_loop_detected',
  'force_innovation_after_repair_loop',
];

function hasOpportunitySignal(signals) {
  const list = Array.isArray(signals) ? signals : [];
  for (let i = 0; i < OPPORTUNITY_SIGNALS.length; i++) {
    if (list.includes(OPPORTUNITY_SIGNALS[i])) return true;
  }
  return false;
}

// Build a de-duplication set from recent evolution events.
// Returns an object: { suppressedSignals: Set<string>, recentIntents: string[], consecutiveRepairCount: number }
function analyzeRecentHistory(recentEvents) {
  if (!Array.isArray(recentEvents) || recentEvents.length === 0) {
    return { suppressedSignals: new Set(), recentIntents: [], consecutiveRepairCount: 0 };
  }
  // Take only the last 10 events
  const recent = recentEvents.slice(-10);

  // Count consecutive same-intent runs at the tail
  let consecutiveRepairCount = 0;
  for (let i = recent.length - 1; i >= 0; i--) {
    if (recent[i].intent === 'repair') {
      consecutiveRepairCount++;
    } else {
      break;
    }
  }

  // Count signal frequency in last 8 events: signal -> count
  const signalFreq = {};
  const geneFreq = {};
  const tail = recent.slice(-8);
  for (let j = 0; j < tail.length; j++) {
    const evt = tail[j];
    const sigs = Array.isArray(evt.signals) ? evt.signals : [];
    for (let k = 0; k < sigs.length; k++) {
      const s = String(sigs[k]);
      // Normalize: ignore errsig details for frequency counting
      const key = s.startsWith('errsig:') ? 'errsig' : s.startsWith('recurring_errsig') ? 'recurring_errsig' : s;
      signalFreq[key] = (signalFreq[key] || 0) + 1;
    }
    const genes = Array.isArray(evt.genes_used) ? evt.genes_used : [];
    for (let g = 0; g < genes.length; g++) {
      geneFreq[String(genes[g])] = (geneFreq[String(genes[g])] || 0) + 1;
    }
  }

  // Suppress signals that appeared in 3+ of the last 8 events (they are being over-processed)
  const suppressedSignals = new Set();
  const entries = Object.entries(signalFreq);
  for (let ei = 0; ei < entries.length; ei++) {
    if (entries[ei][1] >= 3) {
      suppressedSignals.add(entries[ei][0]);
    }
  }

  const recentIntents = recent.map(e => e.intent || 'unknown');

  // Count empty cycles (blast_radius.files === 0) in last 8 events.
  let emptyCycleCount = 0;
  for (let ec = 0; ec < tail.length; ec++) {
    const br = tail[ec].blast_radius;
    const em = tail[ec].meta && tail[ec].meta.empty_cycle;
    if (em || (br && br.files === 0 && br.lines === 0)) {
      emptyCycleCount++;
    }
  }

  // Count consecutive empty cycles at the tail
  let consecutiveEmptyCycles = 0;
  for (let se = recent.length - 1; se >= 0; se--) {
    const seBr = recent[se].blast_radius;
    const seEm = recent[se].meta && recent[se].meta.empty_cycle;
    if (seEm || (seBr && seBr.files === 0 && seBr.lines === 0)) {
      consecutiveEmptyCycles++;
    } else {
      break;
    }
  }

  // Count consecutive failures at the tail
  let consecutiveFailureCount = 0;
  for (let cf = recent.length - 1; cf >= 0; cf--) {
    const outcome = recent[cf].outcome;
    if (outcome && outcome.status === 'failed') {
      consecutiveFailureCount++;
    } else {
      break;
    }
  }

  // Count total failures in last 8 events
  let recentFailureCount = 0;
  for (let rf = 0; rf < tail.length; rf++) {
    const rfOut = tail[rf].outcome;
    if (rfOut && rfOut.status === 'failed') recentFailureCount++;
  }

  return {
    suppressedSignals,
    recentIntents,
    consecutiveRepairCount,
    emptyCycleCount,
    consecutiveEmptyCycles,
    consecutiveFailureCount,
    recentFailureCount,
    recentFailureRatio: tail.length > 0 ? recentFailureCount / tail.length : 0,
    signalFreq,
    geneFreq,
  };
}

function extractSignals({ recentSessionTranscript, todayLog, memorySnippet, userSnippet, recentEvents }) {
  let signals = [];
  const corpus = [
    String(recentSessionTranscript || ''),
    String(todayLog || ''),
    String(memorySnippet || ''),
    String(userSnippet || ''),
  ].join('\n');
  const lower = corpus.toLowerCase();

  // Analyze recent evolution history for de-duplication
  const history = analyzeRecentHistory(recentEvents || []);

  // --- Defensive signals (errors, missing resources) ---

  const errorHit = /\[error\]|error:|exception:|iserror":true|"status":\s*"error"|"status":\s*"failed"/.test(lower);
  if (errorHit) signals.push('log_error');

  // Error signature
  try {
    const lines = corpus
      .split('\n')
      .map(l => String(l || '').trim())
      .filter(Boolean);

    const errLine =
      lines.find(l => /\b(typeerror|referenceerror|syntaxerror)\b\s*:|error\s*:|exception\s*:|\[error/i.test(l)) ||
      null;

    if (errLine) {
      const clipped = errLine.replace(/\s+/g, ' ').slice(0, 260);
      signals.push('errsig:' + clipped);
    }
  } catch (e) {}

  if (lower.includes('memory.md missing')) signals.push('memory_missing');
  if (lower.includes('user.md missing')) signals.push('user_missing');
  if (lower.includes('key missing')) signals.push('integration_key_missing');
  if (lower.includes('no session logs found') || lower.includes('no jsonl files')) signals.push('session_logs_missing');
  if (lower.includes('path.resolve(__dirname, \'../../../')) signals.push('path_outside_workspace');

  // Protocol-specific drift signals
  if (lower.includes('prompt') && !lower.includes('evolutionevent')) signals.push('protocol_drift');

  // --- Recurring error detection ---
  try {
    const errorCounts = {};
    const errPatterns = corpus.match(/(?:LLM error|"error"|"status":\s*"error")[^}]{0,200}/gi) || [];
    for (let ep = 0; ep < errPatterns.length; ep++) {
      const key = errPatterns[ep].replace(/\s+/g, ' ').slice(0, 100);
      errorCounts[key] = (errorCounts[key] || 0) + 1;
    }
    const recurringErrors = Object.entries(errorCounts).filter(e => e[1] >= 3);
    if (recurringErrors.length > 0) {
      signals.push('recurring_error');
      const topErr = recurringErrors.sort((a, b) => b[1] - a[1])[0];
      signals.push('recurring_errsig(' + topErr[1] + 'x):' + topErr[0].slice(0, 150));
    }
  } catch (e) {}

  // --- Unsupported input type ---
  if (/unsupported mime|unsupported.*type|invalid.*mime/i.test(lower)) {
    signals.push('unsupported_input_type');
  }

  // --- Opportunity signals ---

  if (/\b(add|implement|create|build|make|develop|write|design)\b[^.?!\n]{3,60}\b(feature|function|module|capability|tool|support|endpoint|command|option|mode)\b/i.test(corpus)) {
    signals.push('user_feature_request');
  }
  if (/\b(i want|i need|we need|please add|can you add|could you add|let'?s add)\b/i.test(lower)) {
    signals.push('user_feature_request');
  }

  if (/\b(should be|could be better|improve|enhance|upgrade|refactor|clean up|simplify|streamline)\b/i.test(lower)) {
    if (!errorHit) signals.push('user_improvement_suggestion');
  }

  if (/\b(slow|timeout|timed?\s*out|latency|bottleneck|took too long|performance issue|high cpu|high memory|oom|out of memory)\b/i.test(lower)) {
    signals.push('perf_bottleneck');
  }

  if (/\b(not supported|cannot|doesn'?t support|no way to|missing feature|unsupported|not available|not implemented|no support for)\b/i.test(lower)) {
    if (!signals.includes('memory_missing') && !signals.includes('user_missing') && !signals.includes('session_logs_missing')) {
      signals.push('capability_gap');
    }
  }

  // --- Signal prioritization ---
  let actionable = signals.filter(s => {
    return s !== 'user_missing' && s !== 'memory_missing' && s !== 'session_logs_missing';
  });
  if (actionable.length > 0) {
    signals = actionable;
  }

  // --- De-duplication ---
  if (history.suppressedSignals.size > 0) {
    const beforeDedup = signals.length;
    signals = signals.filter(s => {
      const key = s.startsWith('errsig:') ? 'errsig' : s.startsWith('recurring_errsig') ? 'recurring_errsig' : s;
      return !history.suppressedSignals.has(key);
    });
    if (beforeDedup > 0 && signals.length === 0) {
      signals.push('evolution_stagnation_detected');
      signals.push('stable_success_plateau');
    }
  }

  // --- Force innovation after 3+ consecutive repairs ---
  if (history.consecutiveRepairCount >= 3) {
    signals = signals.filter(s => {
      return s !== 'log_error' && !s.startsWith('errsig:') && !s.startsWith('recurring_errsig');
    });
    if (signals.length === 0) {
      signals.push('repair_loop_detected');
      signals.push('stable_success_plateau');
    }
    signals.push('force_innovation_after_repair_loop');
  }

  // --- Force innovation after too many empty cycles ---
  if (history.emptyCycleCount >= 4) {
    signals = signals.filter(s => {
      return s !== 'log_error' && !s.startsWith('errsig:') && !s.startsWith('recurring_errsig');
    });
    if (!signals.includes('empty_cycle_loop_detected')) signals.push('empty_cycle_loop_detected');
    if (!signals.includes('stable_success_plateau')) signals.push('stable_success_plateau');
  }

  // --- Saturation detection ---
  if (history.consecutiveEmptyCycles >= 5) {
    if (!signals.includes('force_steady_state')) signals.push('force_steady_state');
    if (!signals.includes('evolution_saturation')) signals.push('evolution_saturation');
  } else if (history.consecutiveEmptyCycles >= 3) {
    if (!signals.includes('evolution_saturation')) signals.push('evolution_saturation');
  }

  // --- Failure streak awareness ---
  if (history.consecutiveFailureCount >= 3) {
    signals.push('consecutive_failure_streak_' + history.consecutiveFailureCount);
    if (history.consecutiveFailureCount >= 5) {
      signals.push('failure_loop_detected');
      const gfEntries = Object.entries(history.geneFreq);
      let topGene = null;
      let topGeneCount = 0;
      for (let gfi = 0; gfi < gfEntries.length; gfi++) {
        if (gfEntries[gfi][1] > topGeneCount) {
          topGeneCount = gfEntries[gfi][1];
          topGene = gfEntries[gfi][0];
        }
      }
      if (topGene) {
        signals.push('ban_gene:' + topGene);
      }
    }
  }

  // High failure ratio
  if (history.recentFailureRatio >= 0.75) {
    signals.push('high_failure_ratio');
    signals.push('force_innovation_after_repair_loop');
  }

  // Default signal if none
  if (signals.length === 0) {
    signals.push('stable_success_plateau');
  }

  return Array.from(new Set(signals));
}

module.exports = {
  extractSignals,
  hasOpportunitySignal,
  analyzeRecentHistory,
  OPPORTUNITY_SIGNALS
};
