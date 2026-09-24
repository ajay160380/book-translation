import { defineConfig } from "@neon/config/v1";

export default defineConfig({
  buckets: {
    media: { access: "public_read" }
  }
});
