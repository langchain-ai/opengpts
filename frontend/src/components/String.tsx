import { MarkedOptions, marked } from "marked";
import DOMPurify from "dompurify";
import { cn } from "../utils/cn";

const OPTIONS: MarkedOptions = {
  gfm: true,
  breaks: true,
};

export function StringViewer(props: {
  value: string;
  className?: string;
  markdown?: boolean;
}) {
  return props.markdown ? (
    <div
      className={cn("text-gray-900 prose", props.className)}
      dangerouslySetInnerHTML={{
        __html: DOMPurify.sanitize(marked(props.value, OPTIONS)).trim(),
      }}
    />
  ) : (
    <div className={cn("text-gray-900 prose", props.className)}>
      {props.value}
    </div>
  );
}
