import { cn } from "../../lib/utils";


// Variantes de badge
const badgeVariants = (variant = "default") => {
  const baseClasses = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-gray-200 focus:ring-offset-2";

  const variantClasses = {
    default: "border-transparent bg-blue-600 text-white hover:bg-blue-600/80",
    secondary: "border-transparent bg-gray-100 text-gray-800 hover:bg-gray-200/80",
    destructive: "border-transparent bg-red-600 text-white hover:bg-red-600/80",
    outline: "border-gray-300 text-gray-900 bg-transparent",
  };

  return cn(baseClasses, variantClasses[variant] || variantClasses.default);
};

// Composant Badge
function Badge({ className, variant = "default", ...props }) {
  return (
    <div className={cn(badgeVariants(variant), className)} {...props} />
  );
}

export { Badge, badgeVariants };