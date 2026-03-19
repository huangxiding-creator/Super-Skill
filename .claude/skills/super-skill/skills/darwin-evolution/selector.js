/**
 * GEP Selector Module for Super-Skill Darwin Evolution
 * Adapted from autogame-17/evolver (MIT License)
 *
 * Gene and Capsule selection based on signal matching.
 */

function matchPatternToSignals(pattern, signals) {
  if (!pattern || !signals || signals.length === 0) return false;
  const p = String(pattern);
  const sig = signals.map(s => String(s));

  const regexLike = p.length >= 2 && p.startsWith('/') && p.lastIndexOf('/') > 0;
  if (regexLike) {
    const lastSlash = p.lastIndexOf('/');
    const body = p.slice(1, lastSlash);
    const flags = p.slice(lastSlash + 1);
    try {
      const re = new RegExp(body, flags || 'i');
      return sig.some(s => re.test(s));
    } catch (e) {
      // fallback to substring
    }
  }

  const needle = p.toLowerCase();
  return sig.some(s => s.toLowerCase().includes(needle));
}

function scoreGene(gene, signals) {
  if (!gene || gene.type !== 'Gene') return 0;
  const patterns = Array.isArray(gene.signals_match) ? gene.signals_match : [];
  if (patterns.length === 0) return 0;
  let score = 0;
  for (const pat of patterns) {
    if (matchPatternToSignals(pat, signals)) score += 1;
  }
  return score;
}

// Population-size-dependent drift intensity.
function computeDriftIntensity(opts) {
  let driftEnabled = !!(opts && opts.driftEnabled);

  let effectivePopulationSize = opts && Number.isFinite(Number(opts.effectivePopulationSize))
    ? Number(opts.effectivePopulationSize)
    : null;

  let genePoolSize = opts && Number.isFinite(Number(opts.genePoolSize))
    ? Number(opts.genePoolSize)
    : null;

  let ne = effectivePopulationSize || genePoolSize || null;

  if (driftEnabled) {
    return ne && ne > 1 ? Math.min(1, 1 / Math.sqrt(ne) + 0.3) : 0.7;
  }

  if (ne != null && ne > 0) {
    return Math.min(1, 1 / Math.sqrt(ne));
  }

  return 0;
}

function selectGene(genes, signals, opts) {
  const bannedGeneIds = opts && opts.bannedGeneIds ? opts.bannedGeneIds : new Set();
  const driftEnabled = !!(opts && opts.driftEnabled);
  const preferredGeneId = opts && typeof opts.preferredGeneId === 'string' ? opts.preferredGeneId : null;

  const driftIntensity = computeDriftIntensity({
    driftEnabled,
    effectivePopulationSize: opts && opts.effectivePopulationSize,
    genePoolSize: genes ? genes.length : 0,
  });
  const useDrift = driftEnabled || driftIntensity > 0.15;

  const scored = genes
    .map(g => ({ gene: g, score: scoreGene(g, signals) }))
    .filter(x => x.score > 0)
    .sort((a, b) => b.score - a.score);

  if (scored.length === 0) return { selected: null, alternatives: [], driftIntensity };

  // Memory graph preference
  if (preferredGeneId) {
    const preferred = scored.find(x => x.gene && x.gene.id === preferredGeneId);
    if (preferred && (useDrift || !bannedGeneIds.has(preferredGeneId))) {
      const rest = scored.filter(x => x.gene && x.gene.id !== preferredGeneId);
      const filteredRest = useDrift ? rest : rest.filter(x => x.gene && !bannedGeneIds.has(x.gene.id));
      return {
        selected: preferred.gene,
        alternatives: filteredRest.slice(0, 4).map(x => x.gene),
        driftIntensity,
      };
    }
  }

  // Low-efficiency suppression
  const filtered = useDrift ? scored : scored.filter(x => x.gene && !bannedGeneIds.has(x.gene.id));
  if (filtered.length === 0) return { selected: null, alternatives: scored.slice(0, 4).map(x => x.gene), driftIntensity };

  // Stochastic selection under drift
  let selectedIdx = 0;
  if (driftIntensity > 0 && filtered.length > 1 && Math.random() < driftIntensity) {
    let topN = Math.min(filtered.length, Math.max(2, Math.ceil(filtered.length * driftIntensity)));
    selectedIdx = Math.floor(Math.random() * topN);
  }

  return {
    selected: filtered[selectedIdx].gene,
    alternatives: filtered.filter((_, i) => i !== selectedIdx).slice(0, 4).map(x => x.gene),
    driftIntensity,
  };
}

function selectCapsule(capsules, signals) {
  const scored = (capsules || [])
    .map(c => {
      const triggers = Array.isArray(c.trigger) ? c.trigger : [];
      const score = triggers.reduce((acc, t) => (matchPatternToSignals(t, signals) ? acc + 1 : acc), 0);
      return { capsule: c, score };
    })
    .filter(x => x.score > 0)
    .sort((a, b) => b.score - a.score);
  return scored.length ? scored[0].capsule : null;
}

function selectGeneAndCapsule({ genes, capsules, signals, memoryAdvice, driftEnabled }) {
  const bannedGeneIds =
    memoryAdvice && memoryAdvice.bannedGeneIds instanceof Set ? memoryAdvice.bannedGeneIds : new Set();
  const preferredGeneId = memoryAdvice && memoryAdvice.preferredGeneId ? memoryAdvice.preferredGeneId : null;

  const { selected, alternatives, driftIntensity } = selectGene(genes, signals, {
    bannedGeneIds,
    preferredGeneId,
    driftEnabled: !!driftEnabled,
  });
  const capsule = selectCapsule(capsules, signals);
  const selector = buildSelectorDecision({
    gene: selected,
    capsule,
    signals,
    alternatives,
    memoryAdvice,
    driftEnabled,
    driftIntensity,
  });
  return {
    selectedGene: selected,
    capsuleCandidates: capsule ? [capsule] : [],
    selector,
    driftIntensity,
  };
}

function buildSelectorDecision({ gene, capsule, signals, alternatives, memoryAdvice, driftEnabled, driftIntensity }) {
  const reason = [];
  if (gene) reason.push('signals match gene.signals_match');
  if (capsule) reason.push('capsule trigger matches signals');
  if (!gene) reason.push('no matching gene found; new gene may be required');
  if (signals && signals.length) reason.push(`signals: ${signals.join(', ')}`);

  if (memoryAdvice && Array.isArray(memoryAdvice.explanation) && memoryAdvice.explanation.length) {
    reason.push(`memory_graph: ${memoryAdvice.explanation.join(' | ')}`);
  }
  if (driftEnabled) {
    reason.push('random_drift_override: true');
  }
  if (Number.isFinite(driftIntensity) && driftIntensity > 0) {
    reason.push(`drift_intensity: ${driftIntensity.toFixed(3)}`);
  }

  return {
    selected: gene ? gene.id : null,
    intent: gene ? gene.category : 'innovate',
    reason,
    alternatives: Array.isArray(alternatives) ? alternatives.map(g => g.id) : [],
  };
}

module.exports = {
  selectGeneAndCapsule,
  selectGene,
  selectCapsule,
  buildSelectorDecision,
  matchPatternToSignals,
  scoreGene,
  computeDriftIntensity,
};
