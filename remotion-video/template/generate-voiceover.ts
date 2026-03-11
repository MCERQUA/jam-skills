import { writeFileSync, mkdirSync, existsSync } from "fs";
import { execSync } from "child_process";

// ============================================================
// Groq Orpheus TTS Voiceover Generator
// ============================================================
// Usage: GROQ_API_KEY=$GROQ_API_KEY node --strip-types generate-voiceover.ts
//
// Voices: troy (male), austin (male), daniel (male),
//   autumn (female), diana (female), hannah (female)
//
// Vocal directions: [cheerful], [professionally], [whisper],
//   [excited], [dramatic], [warm], [confidently], [sarcastic]
// ============================================================

const GROQ_API_KEY = process.env.GROQ_API_KEY;
if (!GROQ_API_KEY) {
  console.error("ERROR: GROQ_API_KEY environment variable is required");
  process.exit(1);
}

// ── Edit these ──────────────────────────────────────────────
const VOICE = "troy";
const OUTPUT_DIR = "public/voiceover";

const scenes: Array<{ id: string; text: string }> = [
  { id: "scene-01", text: "[professionally] Welcome to our video." },
  { id: "scene-02", text: "Here is the main content." },
  { id: "scene-03", text: "[warm] Thanks for watching!" },
];
// ────────────────────────────────────────────────────────────

async function generateAudio(text: string, outputPath: string): Promise<void> {
  const wavPath = outputPath.replace(/\.mp3$/, ".wav");
  console.log(`Generating: ${outputPath}`);

  const response = await fetch("https://api.groq.com/openai/v1/audio/speech", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${GROQ_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "canopylabs/orpheus-v1-english",
      voice: VOICE,
      input: text,
      response_format: "wav",
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Groq TTS failed (${response.status}): ${err}`);
  }

  const buffer = Buffer.from(await response.arrayBuffer());
  writeFileSync(wavPath, buffer);

  // Convert wav → mp3 (Orpheus only outputs wav)
  execSync(`ffmpeg -y -i "${wavPath}" -codec:a libmp3lame -q:a 2 "${outputPath}" 2>/dev/null`);
  // Clean up wav
  execSync(`rm -f "${wavPath}"`);

  const mp3Size = existsSync(outputPath)
    ? (require("fs").statSync(outputPath).size / 1024).toFixed(1)
    : "?";
  console.log(`  ✓ ${outputPath} (${mp3Size} KB)`);
}

async function main(): Promise<void> {
  if (!existsSync(OUTPUT_DIR)) {
    mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  for (const scene of scenes) {
    await generateAudio(scene.text, `${OUTPUT_DIR}/${scene.id}.mp3`);
  }

  // Print durations for frame calculation
  console.log("\nDurations (for frame calculation at 30fps):");
  for (const scene of scenes) {
    const mp3 = `${OUTPUT_DIR}/${scene.id}.mp3`;
    try {
      const dur = execSync(
        `ffprobe -v error -show_entries format=duration -of csv=p=0 "${mp3}"`,
      )
        .toString()
        .trim();
      const frames = Math.ceil(parseFloat(dur) * 30) + 30;
      console.log(`  ${scene.id}: ${dur}s → ${frames} frames (incl. 30 transition overlap)`);
    } catch {
      console.log(`  ${scene.id}: could not read duration`);
    }
  }

  console.log(`\nDone! ${scenes.length} audio files generated in ${OUTPUT_DIR}/`);
}

main().catch((err) => {
  console.error("Fatal:", err);
  process.exit(1);
});
