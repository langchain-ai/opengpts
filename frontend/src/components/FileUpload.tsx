import { useMemo } from "react";
import { DropzoneState } from "react-dropzone";
import { XCircleIcon } from "@heroicons/react/24/outline";

const baseStyle = {
  flex: 1,
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  padding: "20px",
  borderWidth: 2,
  borderRadius: 2,
  borderColor: "#eeeeee",
  borderStyle: "dashed",
  backgroundColor: "#fafafa",
  color: "#bdbdbd",
  outline: "none",
  transition: "border .24s ease-in-out",
};

const focusedStyle = {
  borderColor: "#2196f3",
};

const acceptStyle = {
  borderColor: "#00e676",
};

const rejectStyle = {
  borderColor: "#ff1744",
};

function Label(props: { id: string; title: string }) {
  return (
    <label
      htmlFor={props.id}
      className="block font-medium leading-6 text-gray-400 mb-2"
    >
      {props.title}
    </label>
  );
}

export function FileUploadDropzone(props: {
  state: DropzoneState;
  files: File[];
  setFiles: React.Dispatch<React.SetStateAction<File[]>>;
}) {
  const { getRootProps, getInputProps, fileRejections } = props.state;

  const files = props.files.map((file, i) => (
    <li key={i}>
      {file.name} - {file.size} bytes
      <span
        className="not-prose ml-2  inline-flex items-center rounded-full px-1 py-1 text-xs font-medium cursor-pointer bg-gray-50 text-gray-600 relative top-[1px]"
        onClick={() =>
          props.setFiles((files) => files.filter((f) => f !== file))
        }
      >
        <XCircleIcon className="h-4 w-4" />
      </span>
    </li>
  ));

  const style = useMemo(
    () =>
      ({
        ...baseStyle,
        ...(props.state.isFocused ? focusedStyle : {}),
        ...(props.state.isDragAccept ? acceptStyle : {}),
        ...(props.state.isDragReject ? rejectStyle : {}),
      } as React.CSSProperties),
    [props.state.isFocused, props.state.isDragAccept, props.state.isDragReject]
  );

  return (
    <section className="">
      <aside>
        <Label id="files" title="Files" />
        <div className="prose">
          <ul>{files}</ul>
        </div>
      </aside>
      <div {...getRootProps({ style })}>
        <input {...getInputProps()} />
        <p>
          Drag n' drop some files here, or click to select files.
          <br />
          Accepted files: .txt, .csv, .html, .docx, .pdf. 
          <br />
          No file should exceed 10 MB.
        </p>
        {fileRejections.length > 0 && (
          <div className="flex items-center rounded-md bg-yellow-50 mt-4 px-2 py-1 text-xs font-medium text-yellow-800 ring-1 ring-inset ring-yellow-600/20 prose">
            <ul>
              {fileRejections.map((reject, i) => (
                <li key={i} className="break-all">
                  {reject.file.name} - {reject.errors[0].message}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
