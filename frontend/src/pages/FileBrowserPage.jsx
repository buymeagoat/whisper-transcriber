import { useState } from "react";
import PageContainer from "../components/PageContainer";
import FileBrowser from "../components/FileBrowser";

export default function FileBrowserPage() {
  const [folder, setFolder] = useState("logs");

  return (
    <PageContainer>
      <h2 className="page-title">File Browser</h2>
      <div style={{ marginTop: "1rem", marginBottom: "1rem" }}>
        <label>
          Folder:
          <select
            value={folder}
            onChange={(e) => setFolder(e.target.value)}
            style={{ marginLeft: "0.5rem" }}
          >
            <option value="logs">logs</option>
            <option value="uploads">uploads</option>
            <option value="transcripts">transcripts</option>
          </select>
        </label>
      </div>
      <FileBrowser folder={folder} />
    </PageContainer>
  );
}
