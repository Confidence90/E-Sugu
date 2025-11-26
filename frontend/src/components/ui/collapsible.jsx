import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";

const Collapsible = CollapsiblePrimitive.Root;

const CollapsibleTrigger = React.forwardRef(({ className, children, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleTrigger
    ref={ref}
    className={`
      flex items-center justify-between
      py-2 px-4
      w-full
      focus-visible:outline-none
      focus-visible:ring-2 focus-visible:ring-ring
      focus-visible:ring-offset-2 focus-visible:ring-offset-background
      transition-colors
      hover:bg-accent hover:text-accent-foreground
      ${className || ''}
    `}
    {...props}
  >
    {children}
    <ChevronDownIcon className="h-4 w-4 transition-transform duration-200 group-data-[state=open]:rotate-180" />
  </CollapsiblePrimitive.CollapsibleTrigger>
));

const CollapsibleContent = React.forwardRef(({ className, children, ...props }, ref) => (
  <CollapsiblePrimitive.CollapsibleContent
    ref={ref}
    className={`
      overflow-hidden
      data-[state=open]:animate-accordion-down
      data-[state=closed]:animate-accordion-up
      ${className || ''}
    `}
    {...props}
  >
    <div className="pb-4 px-4">{children}</div>
  </CollapsiblePrimitive.CollapsibleContent>
));

export { Collapsible, CollapsibleTrigger, CollapsibleContent };