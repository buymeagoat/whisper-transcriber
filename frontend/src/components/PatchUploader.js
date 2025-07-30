import React from "react";

export default function PatchUploader() {
  return (
    <div style={{ marginTop: "1rem", color: "#a1a1aa" }}>
      Patch logs are generated automatically from Codex Analyst GPT prompts and
      saved under <code>docs/patch_logs/</code>. Manual ZIP uploads are no
      longer needed.
    </div>
  );
}
