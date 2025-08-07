import { motion, AnimatePresence } from "framer-motion";
import Lottie from "lottie-react";
import videoLoader from "@/../public/animation.json";

interface LoadingOverlayProps {
  isVisible: boolean;
}

export default function LoadingOverlay({ isVisible}: LoadingOverlayProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="grow relative inset-0 z-10 flex items-center justify-center bg-sidebar rounded-xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          <div className="w-25 h-25">
            <Lottie animationData={videoLoader} loop autoplay />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
