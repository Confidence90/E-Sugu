import React from 'react';
import * as CheckboxPrimitive from '@radix-ui/react-checkbox';
import { Check } from 'lucide-react';

const Checkbox = React.forwardRef(({ className, ...props }, ref) => (
  <CheckboxPrimitive.Root
    ref={ref}
    className={`
      peer
      h-4 w-4
      shrink-0
      rounded-sm
      border border-border
      focus:outline-none
      focus:ring-2 focus:ring-ring
      focus:ring-offset-2 focus:ring-offset-background
      disabled:cursor-not-allowed disabled:opacity-50
      data-[state=checked]:border-primary
      data-[state=checked]:bg-primary
      data-[state=checked]:text-primary-foreground
      transition-colors
      ${className || ''}
    `}
    {...props}
  >
    <CheckboxPrimitive.Indicator className="flex items-center justify-center text-current">
      <Check className="h-3 w-3" />
    </CheckboxPrimitive.Indicator>
  </CheckboxPrimitive.Root>
));

Checkbox.displayName = 'Checkbox';

export { Checkbox };