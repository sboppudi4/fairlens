import { useCallback } from "react";
import { useDropzone, FileRejection } from "react-dropzone";
import { motion } from "framer-motion";
import { CheckCircle2, FileWarning, Loader2, UploadCloud } from "lucide-react";
import { formatBytes } from "@/utils/formatters";

export interface FileDropzoneProps {
  onAccept: (file: File) => void;
  isUploading?: boolean;
  uploadedName?: string | null;
  errorMessage?: string | null;
  maxSizeMB?: number;
}

export default function FileDropzone({
  onAccept,
  isUploading = false,
  uploadedName = null,
  errorMessage = null,
  maxSizeMB = 50,
}: FileDropzoneProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted[0]) onAccept(accepted[0]);
    },
    [onAccept],
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"] },
    multiple: false,
    maxSize: maxSizeMB * 1024 * 1024,
  });

  const rejectionMsg = fileRejections[0] ? rejectionToMessage(fileRejections[0]) : null;
  const message = errorMessage ?? rejectionMsg;

  return (
    <motion.div
      animate={message ? { x: [0, -6, 6, -4, 4, 0] } : {}}
      transition={{ duration: 0.35 }}
    >
      <div
        {...getRootProps()}
        role="button"
        tabIndex={0}
        aria-label="Upload CSV file"
        className={[
          "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors",
          isDragActive ? "border-accent bg-accent/5" : "border-border",
          message ? "border-danger/60" : "",
          uploadedName ? "border-success/60" : "",
        ].join(" ")}
      >
        <input {...getInputProps()} />
        {isUploading ? (
          <div className="flex flex-col items-center gap-3 text-muted">
            <Loader2 className="w-8 h-8 animate-spin text-accent" />
            <span>Uploading…</span>
          </div>
        ) : uploadedName ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle2 className="w-8 h-8 text-success" />
            <div>
              <div className="font-medium">{uploadedName}</div>
              <div className="text-xs text-muted">Click to replace</div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 text-muted">
            <UploadCloud className="w-8 h-8 text-accent" />
            <div>
              <div className="font-medium text-fg">
                Drop your CSV here or <span className="text-accent">click to browse</span>
              </div>
              <div className="text-xs mt-1">
                Up to {formatBytes(maxSizeMB * 1024 * 1024)} · UTF-8 · header row required
              </div>
            </div>
          </div>
        )}
      </div>
      {message && (
        <div role="alert" className="mt-2 flex items-center gap-2 text-sm text-danger">
          <FileWarning className="w-4 h-4" />
          {message}
        </div>
      )}
    </motion.div>
  );
}

function rejectionToMessage(r: FileRejection): string {
  const code = r.errors[0]?.code;
  if (code === "file-too-large") return "File exceeds the size limit.";
  if (code === "file-invalid-type") return "Only .csv files are accepted.";
  return r.errors[0]?.message ?? "Could not accept this file.";
}
