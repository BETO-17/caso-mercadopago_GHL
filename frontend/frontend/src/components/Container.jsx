function Container({ children, className = "", padding = "p-8", background = "bg-bg-sidebar" }) {
  return (
    <div className={`border-2 border-bg-sidebar rounded-xl ${padding} ${background} ${className}`}>
      {children}
    </div>
  );
}

export default Container;
