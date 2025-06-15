import { Link } from "react-router";
import { ArrowLeft } from "lucide-react";

export const BackBtn = () => {
  return (
    <Link 
      to="/" 
      className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors duration-200"
    >
      <ArrowLeft size={20} />
      <span>Back</span>
    </Link>
  );
}