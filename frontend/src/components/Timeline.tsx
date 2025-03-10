import { useState } from "react";
import { Slider } from "@mui/material";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ClockIcon,
} from "@heroicons/react/24/outline";
import { cn } from "../utils/cn";
import { History } from "../hooks/useHistories";

export function Timeline(props: {
  disabled: boolean;
  histories: History[];
  activeHistoryIndex: number;
  onChange?: (newValue: number) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="flex items-center">
      <button
        className="flex items-center p-2 text-sm"
        type="submit"
        disabled={props.disabled}
        onClick={() => setExpanded((expanded) => !expanded)}
      >
        <ClockIcon className="h-4 w-4 mr-1 rounded-md shrink-0" />
        <span className="text-gray-900 font-semibold shrink-0">
          Time travel
        </span>
      </button>
      <Slider
        className={cn(
          "w-full shrink transition-max-width duration-200",
          expanded ? " ml-8 mr-8 max-w-full" : " invisible max-w-0",
        )}
        aria-label="Timeline"
        value={props.activeHistoryIndex}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        onChange={(e) => props.onChange?.((e.target as any).value)}
        valueLabelDisplay="auto"
        step={1}
        marks
        min={0}
        max={props.histories.length - 1}
      />
      {expanded ? (
        <ChevronLeftIcon
          className="h-4 w-4 cursor-pointer shrink-0 mr-4"
          onClick={() => setExpanded((expanded) => !expanded)}
        />
      ) : (
        <ChevronRightIcon
          className="h-4 w-4 cursor-pointer shrink-0 mr-4"
          onClick={() => setExpanded((expanded) => !expanded)}
        />
      )}
    </div>
  );
}
