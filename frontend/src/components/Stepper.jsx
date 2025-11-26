export default function Stepper({ steps, currentStep }) {
  return (
    <div className="flex justify-between items-center mb-8">
      {steps.map((step, index) => {
        const isActive = index === currentStep;
        const isDone = index < currentStep;

        return (
          <div
            key={step}
            className="flex-1 flex flex-col items-center relative"
          >
            {/* Pastille */}
            <div
              className={`w-8 h-8 flex items-center justify-center rounded-full border-2 
                ${isDone ? "bg-green-500 border-green-500 text-white" : ""}
                ${isActive ? "border-orange-500 text-orange-500" : ""}
                ${!isActive && !isDone ? "border-gray-300 text-gray-400" : ""}
              `}
            >
              {isDone ? "✓" : index + 1}
            </div>
            <span
              className={`mt-2 text-xs font-medium ${
                isActive ? "text-orange-500" : "text-gray-500"
              }`}
            >
              {step}
            </span>

            {/* Ligne entre pastilles */}
            {index < steps.length - 1 && (
              <div
                className={`absolute top-4 left-1/2 w-full h-0.5 -z-10 
                  ${isDone ? "bg-green-500" : "bg-gray-300"}
                `}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
