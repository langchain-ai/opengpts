import CodeMirror from "@uiw/react-codemirror";
import { json } from "@codemirror/lang-json";
import { EditorView, keymap } from "@codemirror/view";
import { defaultKeymap } from "@codemirror/commands";
import { cn } from "../utils/cn";

export function JsonEditor(props: {
  value?: string;
  onChange?: (data: string) => void;
  height?: string;
}) {
  return (
    <div className="relative flex flex-grow items-stretch">
      <CodeMirror
        value={props.value}
        onChange={props.onChange}
        height={props.height ?? "33vh"}
        className={cn("max-w-full w-full overflow-auto min-w-0")}
        extensions={[
          keymap.of([{ key: "Mod-Enter", run: () => true }, ...defaultKeymap]),
          json(),
          EditorView.lineWrapping,
          EditorView.theme({
            "&.cm-editor": {
              backgroundColor: "transparent",
              transform: "translateX(-1px)",
            },
            "&.cm-focused": {
              outline: "none",
            },
            green: {
              background: "green",
            },
            "& .cm-content": {
              padding: "12px",
            },
            "& .cm-line": {
              fontFamily: "'Fira Code', monospace",
              padding: 0,
              overflowAnchor: "none",
              fontVariantLigatures: "none",
            },
            "& .cm-gutters.cm-gutters": {
              backgroundColor: "transparent",
            },
            "& .cm-lineNumbers .cm-gutterElement.cm-activeLineGutter": {
              marginLeft: "1px",
            },
            "& .cm-lineNumbers": {
              minWidth: "42px",
            },
            "& .cm-foldPlaceholder": {
              padding: "0px 4px",
              color: "hsl(var(--ls-gray-100))",
              backgroundColor: "hsl(var(--divider-500))",
              borderColor: "hsl(var(--divider-700))",
            },
            '& .cm-gutterElement span[title="Fold line"]': {
              transform: "translateY(-4px)",
              display: "inline-block",
            },
          }),
        ]}
      />
    </div>
  );
}
