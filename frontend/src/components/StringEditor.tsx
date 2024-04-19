import { cn } from "../utils/cn";

const COMMON_CLS = cn(
  "text-sm col-[1] row-[1] m-0 resize-none overflow-hidden whitespace-pre-wrap break-words bg-transparent px-2 py-1 rounded shadow-none",
);

export function StringEditor(props: {
  value?: string | null | undefined;
  placeholder?: string;
  className?: string;
  onChange?: (e: string) => void;
  autoFocus?: boolean;
  readOnly?: boolean;
  cursorPointer?: boolean;
  disabled?: boolean;
  fullHeight?: boolean;
}) {
  return (
    <div
      className={
        cn("grid w-full", props.className) +
        (props.fullHeight ? "" : " max-h-80 overflow-auto ")
      }
    >
      <textarea
        className={cn(
          COMMON_CLS,
          "text-transparent caret-black rounded focus:outline-0 focus:ring-0",
        )}
        disabled={props.disabled}
        value={props.value ?? ""}
        rows={1}
        onChange={(e) => {
          const target = e.target as HTMLTextAreaElement;
          props.onChange?.(target.value);
        }}
        placeholder={props.placeholder}
        readOnly={props.readOnly}
        autoFocus={props.autoFocus && !props.readOnly}
      />
      <div
        aria-hidden
        className={cn(COMMON_CLS, "pointer-events-none select-none")}
      >
        {props.value}{" "}
      </div>
    </div>
  );
}
