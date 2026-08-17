# file-storage — Detail Reference

Moved out of SKILL.md in the V4.1.5 progressive-disclosure upgrade (SKILL.md stays under the 490-line budget; this file loads on demand).

## CDN Integration

### CloudFront Configuration

```typescript
import {
  CloudFrontClient,
  CreateInvalidationCommand
} from '@aws-sdk/client-cloudfront';

class CDNService {
  private cloudFront = new CloudFrontClient({ region: process.env.AWS_REGION });
  private distributionId: string;

  constructor(distributionId: string) {
    this.distributionId = distributionId;
  }

  // Invalidate cache after update
  async invalidate(paths: string[]): Promise<void> {
    await this.cloudFront.send(new CreateInvalidationCommand({
      DistributionId: this.distributionId,
      InvalidationBatch: {
        CallerReference: `${Date.now()}`,
        Paths: {
          Quantity: paths.length,
          Items: paths
        }
      }
    }));
  }

  // Get CDN URL
  getUrl(key: string): string {
    return `https://${process.env.CLOUDFRONT_DOMAIN}/${key}`;
  }
}

// Usage after upload
async function uploadWithCacheInvalidation(
  file: Buffer,
  key: string
): Promise<string> {
  const storage = new StorageService(process.env.S3_BUCKET!);
  const cdn = new CDNService(process.env.CLOUDFRONT_DISTRIBUTION_ID!);

  await storage.upload(file, key, 'image/webp');

  // Invalidate CDN cache
  await cdn.invalidate([`/${key}`]);

  return cdn.getUrl(key);
}
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-03-02 | Initial integration with Super-Skill V3.7 |

---

## References

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Cloudflare R2](https://developers.cloudflare.com/r2/)
- [Sharp Documentation](https://sharp.pixelplumbing.com/)
- [Multer Documentation](https://github.com/expressjs/multer)
