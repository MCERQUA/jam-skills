import { writeFileSync, mkdirSync, existsSync } from "fs";

// ============================================================
// Groq TTS Voiceover Generator
// ============================================================
// Usage: GROQ_API_KEY=$GROQ_API_KEY node --strip-types generate-voiceover.ts
//
// Available voices: Fritz-PlayAI, Arista-PlayAI, Atlas-PlayAI,
//   Basil-PlayAI, Briggs-PlayAI, Calista-PlayAI, Celeste-PlayAI,
//   Cheyenne-PlayAI, Chip-PlayAI, Cillian-PlayAI, Deedee-PlayAI,
//   Eleanor-PlayAI, Gail-PlayAI, Indira-PlayAI, Jennifer-PlayAI,
//   Mamaw-PlayAI, Mason-PlayAI, Mikail-PlayAI, Mitch-PlayAI,
//   Nia-PlayAI, Quinn-PlayAI, Ruby-PlayAI, Thunder-PlayAI
// ============================================================

const GROQ_API_KEY = process.env.GROQ_API_KEY;
if (!GROQ_API_KEY) {
  console.error("ERROR: GROQ_API_KEY environment variable is required");
  process.exit(1);
}

// ── Edit these ──────────────────────────────────────────────
const VOICE = "Fritz-PlayAI";
const OUTPUT_DIR = "public/voiceover";

const scenes: Array<{ id: string; text: string }> = [
  { id: "scene-01", text: "Welcome to our video." },
  { id: "scene-02", text: "Here is the main content." },
  { id: "scene-03", text: "Thanks for watching!" },
];
// ────────────────────────────────────────────────────────────

async function generateAudio(text: string, outputPath: string): Promise<void> {
  console.log(`Generating: ${outputPath}`);
  const response = await fetch("https://api.groq.com/openai/v1/audio/speech", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${GROQ_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "playai-tts",
      voice: VOICE,
      input: text,
      response_format: "mp3",
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Groq TTS failed (${response.status}): ${err}`);
  }

  const buffer = Buffer.from(await response.arrayBuffer());
  writeFileSync(outputPath, buffer);
  console.log(`  ✓ ${outputPath} (${(buffer.length / 1024).toFixed(1)} KB)`);
}

async function main(): Promise<void> {
  if (!existsSync(OUTPUT_DIR)) {
    mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  for (const scene of scenes) {
    await generateAudio(scene.text, `${OUTPUT_DIR}/${scene.id}.mp3`);
  }

  console.log(`\nDone! ${scenes.length} audio files generated in ${OUTPUT_DIR}/`);
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
