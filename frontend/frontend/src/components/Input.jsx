function Input({ 
  type = "text", 
  placeholder = "", 
  value, 
  onChange, 
  label,
  className = ""
}) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-text-primary font-medium mb-2 text-base">
          {label}
        </label>
      )}
      <input
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        className={`w-full bg-bg-main text-text-primary placeholder:text-gray-400 placeholder:opacity-60 rounded-lg px-4 py-3 border-none outline-none focus:ring-2 focus:ring-white/20 transition-all ${className}`}
      />
    </div>
  );
}

export default Input;
