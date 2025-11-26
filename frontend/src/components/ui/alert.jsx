import { forwardRef } from 'react';

// Fonction utilitaire pour combiner les classes
function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

// Variantes d'alerte
const alertVariants = (variant) => {
  const baseStyles = "relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-gray-900";
  
  const variants = {
    default: "bg-white text-gray-900 border-gray-200",
    destructive: "border-red-500/50 text-red-500 [&>svg]:text-red-500"
  };

  return cn(baseStyles, variants[variant] || variants.default);
};

// Composant Alert principal
const Alert = forwardRef(({ className, variant = 'default', ...props }, ref) => (
  <div
    ref={ref}
    role="alert"
    className={cn(alertVariants(variant), className)}
    {...props}
  />
));
Alert.displayName = "Alert";

// Composant AlertTitle
const AlertTitle = forwardRef(({ className, ...props }, ref) => (
  <h5
    ref={ref}
    className={cn("mb-1 font-medium leading-none tracking-tight", className)}
    {...props}
  />
));
AlertTitle.displayName = "AlertTitle";

// Composant AlertDescription
const AlertDescription = forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("text-sm [&_p]:leading-relaxed", className)}
    {...props}
  />
));
AlertDescription.displayName = "AlertDescription";

export { Alert, AlertTitle, AlertDescription };