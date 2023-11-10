import { useMemo } from "react";
import { DropzoneState } from "react-dropzone";

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

export function FileUploadDropzone(props: { state: DropzoneState }) {
  const { acceptedFiles, getRootProps, getInputProps } = props.state;

  const files = acceptedFiles.map((file, i) => (
    <li key={i}>
      {file.name} - {file.size} bytes
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
        <ul className="prose mb-2">{files}</ul>
      </aside>
      <div {...getRootProps({ style })}>
        <input {...getInputProps()} />
        <p>
          Drag 'n' drop some files here, or click to select files. Only .txt and
          .csv files are accepted currently.
        </p>
      </div>
    </section>
  );
}
