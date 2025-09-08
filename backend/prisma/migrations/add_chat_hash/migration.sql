-- Add hash column to ChatSession table
ALTER TABLE "ChatSession" ADD COLUMN "hash" TEXT;

-- Generate unique hashes for existing chats
UPDATE "ChatSession" SET "hash" = 'chat_' || id || '_' || EXTRACT(EPOCH FROM "createdAt")::bigint WHERE "hash" IS NULL;

-- Make hash column unique and not null
ALTER TABLE "ChatSession" ALTER COLUMN "hash" SET NOT NULL;
ALTER TABLE "ChatSession" ADD CONSTRAINT "ChatSession_hash_key" UNIQUE ("hash");

-- Add default value for future chats
ALTER TABLE "ChatSession" ALTER COLUMN "hash" SET DEFAULT gen_random_uuid()::text; 