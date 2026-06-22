"use client"
import * as React from "react"
import { Slider as SliderPrimitive } from "@base-ui/react/slider"
import { cn } from "@/lib/utils"

function Slider({
  className,
  value,
  onValueChange,
  min = 0,
  max = 100,
  step = 1,
}: {
  className?: string
  value: number[]
  onValueChange: (value: number[]) => void
  min?: number
  max?: number
  step?: number
}) {
  return (
    <SliderPrimitive.Root
      value={value}
      onValueChange={(v) => onValueChange(v as number[])}
      min={min}
      max={max}
      step={step}
      className={cn("relative flex w-full touch-none items-center select-none", className)}
    >
      <SliderPrimitive.Control className="flex w-full touch-none items-center py-1 select-none">
        <SliderPrimitive.Track className="relative h-1.5 w-full grow rounded-full bg-gray-200 dark:bg-muted select-none">
          <SliderPrimitive.Indicator className="absolute h-full rounded-full bg-amazon-link select-none" />
          <SliderPrimitive.Thumb
            index={0}
            className="block h-4 w-4 rounded-full border-2 border-white bg-amazon-nav shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 select-none"
          />
          <SliderPrimitive.Thumb
            index={1}
            className="block h-4 w-4 rounded-full border-2 border-white bg-amazon-nav shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50 select-none"
          />
        </SliderPrimitive.Track>
      </SliderPrimitive.Control>
    </SliderPrimitive.Root>
  )
}

export { Slider }
