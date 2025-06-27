import React, { useState, useEffect } from "react";
import { useDispatch } from "react-redux";
import { useApi } from "../api";
import { addToast } from "../store";
import { ROUTES } from "../routes";
import Button from "./Button";
import LinkButton from "./LinkButton";
import { List, ListItem } from "./List";
import "./FileBrowser.css";

export default function FileBrowser({ folder, className = "" }) {
  const api = useApi();
  const dispatch = useDispatch();
  const [path, setPath] = useState("");
  const [directories, setDirectories] = useState([]);
  const [files, setFiles] = useState([]);

  const load = async (p) => {
    const params = new URLSearchParams({ folder });
    if (p) params.append("path", p);
    try {
      const data = await api.get(`/admin/browse?${params.toString()}`);
      setDirectories(data.directories);
      setFiles(data.files);
    } catch {
      dispatch(addToast("Failed to load directory", "error"));
    }
  };

  useEffect(() => {
    load(path);
  }, [folder, path]);

  const filePath = (name) => (path ? `${path}/${name}` : name);

  const getViewLink = (name) => {
    const full = filePath(name);
    if (folder === "logs") {
      return `${ROUTES.API}/logs/${encodeURIComponent(full)}`;
    }
    if (folder === "transcripts") {
      const jobId = full.split("/")[0];
      return `${ROUTES.API}/transcript/${encodeURIComponent(jobId)}/view`;
    }
    return `${ROUTES.API}/${folder}/${encodeURIComponent(full)}`;
  };

  const getDownloadLink = (name) => {
    const full = filePath(name);
    if (folder === "transcripts") {
      const jobId = full.split("/")[0];
      return `${ROUTES.API}/jobs/${encodeURIComponent(jobId)}/download`;
    }
    return `${ROUTES.API}/${folder}/${encodeURIComponent(full)}`;
  };

  const handleDelete = async (name) => {
    const confirmed = window.confirm(`Delete ${name}?`);
    if (!confirmed) return;
    try {
      await api.del("/admin/files", {
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder, filename: filePath(name) }),
      });
      dispatch(addToast("File deleted", "success"));
      load(path);
    } catch {
      dispatch(addToast("Failed to delete file", "error"));
    }
  };

  const breadcrumbs = (() => {
    const bc = [{ label: folder, path: "" }];
    if (path) {
      const parts = path.split("/").filter(Boolean);
      let current = "";
      for (const part of parts) {
        current = current ? `${current}/${part}` : part;
        bc.push({ label: part, path: current });
      }
    }
    return bc;
  })();

  return (
    <div className={`file-browser ${className}`.trim()}>
      <div className="file-browser-breadcrumbs">
        {breadcrumbs.map((bc, idx) => (
          <span key={bc.path}>
            {idx > 0 && " / "}
            <a href="#" onClick={(e) => {e.preventDefault(); setPath(bc.path);}}>
              {bc.label || folder}
            </a>
          </span>
        ))}
      </div>
      <List className="file-browser-list">
        {directories.map((dir) => (
          <ListItem
            key={`dir-${dir}`}
            className="file-browser-directory"
            onClick={() => setPath(filePath(dir))}
          >
            {dir}/
          </ListItem>
        ))}
        {files.map((file) => (
          <ListItem key={`file-${file}`} className="file-browser-item">
            {file}
            <LinkButton
              className="file-action"
              href={getViewLink(file)}
              target="_blank"
              rel="noopener noreferrer"
              color="#10b981"
            >
              View
            </LinkButton>
            <LinkButton
              className="file-action"
              href={getDownloadLink(file)}
              target="_blank"
              rel="noopener noreferrer"
              download
              color="#3b82f6"
            >
              Download
            </LinkButton>
            <Button
              className="file-action"
              onClick={() => handleDelete(file)}
              color="#dc2626"
            >
              Delete
            </Button>
          </ListItem>
        ))}
      </List>
    </div>
  );
}
