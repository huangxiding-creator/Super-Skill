---
name: file-storage
description: File handling, storage patterns, and cloud storage integration. Covers local filesystem, S3/Cloudflare R2, file uploads, image processing, and CDN integration.
tags: [storage, s3, files, uploads, images, cdn]
version: 1.0.0
source: Based on AWS S3, Cloudflare R2, Sharp, Multer best practices
integrated-with: super-skill v3.7+
---

# File Storage Skill

This skill provides comprehensive file handling and storage patterns for local and cloud storage, file uploads, image processing, and CDN integration.

## Storage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    FILE STORAGE ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LOCAL STORAGE                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • File system       • Temporary files    • Static files │    │
│  │ • Node.js fs        • Streams            • Permissions  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  CLOUD STORAGE                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • S3/R2/GCS         • Presigned URLs     • Lifecycle    │    │
│  │ • Bucket policies   • Versioning         • Encryption   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  IMAGE PROCESSING                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • Resize/Crop       • Format conversion  • Optimization │    │
│  │ • Sharp             • Cloudflare Images  • AWS Lambda   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  CDN INTEGRATION                                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ • CloudFront        • Cloudflare CDN     • Cache rules  │    │
│  │ • Edge caching      • Invalidations      • Geo-routing  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## File Upload Patterns

### Multer Configuration

```typescript
import multer from 'multer';
import { v4 as uuidv4 } from 'uuid';
import path from 'path';

// Storage configuration
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = `uploads/${req.user.id}`;
    fs.mkdirSync(uploadDir, { recursive: true });
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const ext = path.extname(file.originalname);
    cb(null, `${uuidv4()}${ext}`);
  }
});

// File filter
const fileFilter = (req: Request, file: Express.Multer.File, cb: any) => {
  const allowedMimes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];

  if (allowedMimes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error(`Invalid file type: ${file.mimetype}`), false);
  }
};

// Limits
const limits = {
  fileSize: 10 * 1024 * 1024, // 10MB
  files: 5
};

export const upload = multer({
  storage,
  fileFilter,
  limits
});

// Usage in route
app.post('/upload', upload.array('files', 5), async (req, res) => {
  const files = req.files as Express.Multer.File[];

  const uploadedFiles = await Promise.all(
    files.map(async (file) => {
      // Process and upload to cloud storage
      const cloudUrl = await uploadToS3(file);
      return {
        originalName: file.originalname,
        size: file.size,
        url: cloudUrl
      };
    })
  );

  res.json({ files: uploadedFiles });
});
```

### Memory Storage with Processing

```typescript
import { Readable } from 'stream';

// Memory storage for processing before cloud upload
const memoryStorage = multer.memoryStorage();

export const uploadForProcessing = multer({
  storage: memoryStorage,
  limits: { fileSize: 50 * 1024 * 1024 } // 50MB
});

// Process image and upload
async function processAndUploadImage(
  buffer: Buffer,
  options: ImageProcessOptions = {}
): Promise<UploadResult> {
  const sharp = require('sharp');

  let image = sharp(buffer);

  // Get metadata
  const metadata = await image.metadata();

  // Resize if needed
  if (options.maxWidth || options.maxHeight) {
    image = image.resize(options.maxWidth, options.maxHeight, {
      fit: 'inside',
      withoutEnlargement: true
    });
  }

  // Convert format
  if (options.format) {
    image = image.toFormat(options.format, {
      quality: options.quality || 85
    });
  }

  // Process
  const processedBuffer = await image.toBuffer();

  // Upload to S3
  const key = `images/${uuidv4()}.${options.format || metadata.format}`;
  const url = await uploadToS3(processedBuffer, key, metadata.format);

  return {
    url,
    key,
    width: metadata.width,
    height: metadata.height,
    size: processedBuffer.length
  };
}
```

## S3/Cloudflare R2 Integration

### S3 Client Setup

```typescript
import { S3Client, PutObjectCommand, GetObjectCommand, DeleteObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const s3Client = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!
  }
});

// For Cloudflare R2
const r2Client = new S3Client({
  region: 'auto',
  endpoint: process.env.R2_ENDPOINT,
  credentials: {
    accessKeyId: process.env.R2_ACCESS_KEY_ID!,
    secretAccessKey: process.env.R2_SECRET_ACCESS_KEY!
  }
});

class StorageService {
  private bucket: string;
  private client: S3Client;

  constructor(bucket: string, client: S3Client = s3Client) {
    this.bucket = bucket;
    this.client = client;
  }

  async upload(
    buffer: Buffer,
    key: string,
    contentType: string
  ): Promise<string> {
    await this.client.send(new PutObjectCommand({
      Bucket: this.bucket,
      Key: key,
      Body: buffer,
      ContentType: contentType,
      CacheControl: 'max-age=31536000' // 1 year
    }));

    return this.getUrl(key);
  }

  async uploadFromStream(
    stream: Readable,
    key: string,
    contentType: string
  ): Promise<string> {
    const chunks: Buffer[] = [];

    for await (const chunk of stream) {
      chunks.push(chunk);
    }

    return this.upload(Buffer.concat(chunks), key, contentType);
  }

  async delete(key: string): Promise<void> {
    await this.client.send(new DeleteObjectCommand({
      Bucket: this.bucket,
      Key: key
    }));
  }

  getPublicUrl(key: string): string {
    return `https://${this.bucket}.s3.amazonaws.com/${key}`;
  }

  async getPresignedUploadUrl(
    key: string,
    contentType: string,
    expiresIn: number = 3600
  ): Promise<string> {
    const command = new PutObjectCommand({
      Bucket: this.bucket,
      Key: key,
      ContentType: contentType
    });

    return getSignedUrl(this.client, command, { expiresIn });
  }

  async getPresignedDownloadUrl(
    key: string,
    expiresIn: number = 3600
  ): Promise<string> {
    const command = new GetObjectCommand({
      Bucket: this.bucket,
      Key: key
    });

    return getSignedUrl(this.client, command, { expiresIn });
  }
}
```

### Direct Upload Pattern

```typescript
// Server: Generate presigned URL
app.post('/upload-url', async (req, res) => {
  const { filename, contentType } = req.body;

  const key = `uploads/${req.user.id}/${uuidv4()}-${filename}`;
  const storage = new StorageService(process.env.S3_BUCKET!);

  const uploadUrl = await storage.getPresignedUploadUrl(key, contentType);

  res.json({
    uploadUrl,
    key,
    publicUrl: storage.getPublicUrl(key)
  });
});

// Client: Direct upload to S3
async function uploadFileDirect(file: File): Promise<string> {
  // Get presigned URL
  const { uploadUrl, key, publicUrl } = await fetch('/upload-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: file.name,
      contentType: file.type
    })
  }).then(r => r.json());

  // Upload directly to S3
  await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': file.type },
    body: file
  });

  return publicUrl;
}
```

## Image Processing

### Sharp Integration

```typescript
import sharp from 'sharp';

class ImageProcessor {
  // Generate multiple sizes for responsive images
  async generateResponsiveImages(
    buffer: Buffer,
    baseKey: string
  ): Promise<ResponsiveImageSet> {
    const sizes = [320, 640, 960, 1280, 1920];
    const images: Record<number, string> = {};

    for (const width of sizes) {
      const resized = await sharp(buffer)
        .resize(width, null, {
          fit: 'inside',
          withoutEnlargement: true
        })
        .webp({ quality: 85 })
        .toBuffer();

      const key = `${baseKey}-${width}.webp`;
      images[width] = await this.storage.upload(resized, key, 'image/webp');
    }

    return images;
  }

  // Generate thumbnail
  async generateThumbnail(
    buffer: Buffer,
    size: number = 200
  ): Promise<Buffer> {
    return sharp(buffer)
      .resize(size, size, {
        fit: 'cover',
        position: 'center'
      })
      .webp({ quality: 80 })
      .toBuffer();
  }

  // Extract metadata
  async getMetadata(buffer: Buffer): Promise<ImageMetadata> {
    const metadata = await sharp(buffer).metadata();

    return {
      width: metadata.width,
      height: metadata.height,
      format: metadata.format,
      size: metadata.size,
      hasAlpha: metadata.hasAlpha,
      orientation: metadata.orientation
    };
  }

  // Convert format
  async convert(
    buffer: Buffer,
    format: 'webp' | 'jpeg' | 'png' | 'avif',
    quality: number = 85
  ): Promise<Buffer> {
    return sharp(buffer)
      .toFormat(format, { quality })
      .toBuffer();
  }

  // Add watermark
  async addWatermark(
    imageBuffer: Buffer,
    watermarkBuffer: Buffer,
    position: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left' | 'center' = 'bottom-right'
  ): Promise<Buffer> {
    const image = sharp(imageBuffer);
    const { width, height } = await image.metadata();

    const watermark = await sharp(watermarkBuffer)
      .resize(Math.floor(width! * 0.2))
      .toBuffer();

    const gravityMap = {
      'bottom-right': 'southeast',
      'bottom-left': 'southwest',
      'top-right': 'northeast',
      'top-left': 'northwest',
      'center': 'center'
    };

    return image
      .composite([{
        input: watermark,
        gravity: gravityMap[position] as any,
        blend: 'over'
      }])
      .toBuffer();
  }
}
```

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

## Integration with Super-Skill

### Phase Integration

```yaml
storage_phase_mapping:
  phase_5_design:
    outputs:
      - storage_architecture
      - cdn_strategy
      - upload_requirements

  phase_8_development:
    actions:
      - setup_storage_service
      - implement_upload_api
      - add_image_processing
      - configure_cdn

  phase_11_deployment:
    actions:
      - setup_s3_buckets
      - configure_cloudfront
      - setup_backup
```

## Best Practices Checklist

### Uploads
- [ ] File type validation
- [ ] Size limits enforced
- [ ] Virus scanning (if needed)
- [ ] Unique filenames
- [ ] Progress feedback

### Storage
- [ ] Proper bucket policies
- [ ] Encryption enabled
- [ ] Lifecycle rules set
- [ ] Versioning configured
- [ ] Backup strategy

### Performance
- [ ] CDN configured
- [ ] Cache headers set
- [ ] Images optimized
- [ ] Lazy loading
- [ ] Responsive images

## Deliverables

- Storage service implementation
- Upload API endpoints
- Image processing pipeline
- CDN configuration

---

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
