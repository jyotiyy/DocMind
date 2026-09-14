import { useCallback, useRef, useState } from "react";
import { extractApiErrorMessage, uploadDocuments } from "../services/api";

interface PDFUploaderProps {
  onUploaded: () => void;
}

export function PDFUploader({ onUploaded }: PDFUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    async (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) return;
      const pdfFiles = Array.from(fileList).filter((f) => f.name.toLowerCase().endsWith(".pdf"));
      if (pdfFiles.length === 0) {
        setError("Only PDF files are supported.");
        return;
      }

      setError(null);
      setIsUploading(true);
      try {
        await uploadDocuments(pdfFiles);
        onUploaded();
      } catch (err) {
        setError(extractApiErrorMessage(err));
      } finally {
        setIsUploading(false);
      }
    },
    [onUploaded],
  );

  return (
    <div>
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragging(false);
          handleFiles(e.dataTransfer.files);
        }}
        className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-colors ${
          isDragging
            ? "border-brand-500 bg-brand-50"
            : "border-slate-300 hover:border-brand-400 hover:bg-slate-50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <p className="text-sm font-medium text-slate-700">
          {isUploading ? "Uploading & indexing..." : "Drop PDFs here or click to upload"}
        </p>
        <p className="mt-1 text-xs text-slate-400">Scanned PDFs are OCR&apos;d automatically</p>
      </div>
      {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
    </div>
  );
}
