import React, { useState } from "react";
import { messageService } from "../../services/messageService";

const DOC_TITLES = {
  invoice: "Счёт",
  letter: "Письмо",
  contract: "Договор",
};

/**
 * Renders a document produced by the `generate_document` tool with actions to
 * copy it or download it as DOCX / PDF (rendered server-side, Cyrillic-safe).
 */
const DocumentCard = ({ docType, content }) => {
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState(false);

  const title = DOC_TITLES[docType] || "Документ";

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setError(true);
    }
  };

  const handleDownload = async (format) => {
    try {
      setError(false);
      setBusy(format);
      await messageService.exportDocument({
        format,
        content,
        title,
        filename: title,
      });
    } catch (err) {
      console.error("❌ Document export failed:", err);
      setError(true);
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="document-card">
      <div className="document-card-header">
        <span className="document-card-title">📄 {title}</span>
        <div className="document-card-actions">
          <button type="button" className="doc-btn" onClick={handleCopy}>
            {copied ? "✓ Скопировано" : "Копировать"}
          </button>
          <button
            type="button"
            className="doc-btn"
            onClick={() => handleDownload("docx")}
            disabled={busy !== null}
          >
            {busy === "docx" ? "…" : "Скачать DOCX"}
          </button>
          <button
            type="button"
            className="doc-btn"
            onClick={() => handleDownload("pdf")}
            disabled={busy !== null}
          >
            {busy === "pdf" ? "…" : "Скачать PDF"}
          </button>
        </div>
      </div>
      <pre className="document-card-body">{content}</pre>
      {error && (
        <div className="document-card-error">
          Не удалось выполнить действие. Попробуйте ещё раз.
        </div>
      )}
    </div>
  );
};

export default DocumentCard;
