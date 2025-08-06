// import Lottie from "lottie-react";
// import animationData from "@/../../public/videocam.json";
// import { AnimatePresence, motion } from "framer-motion";

// interface LoadingOverlayProps {
//   isVisible: boolean;
// }

// export default function LoadingOverlay({ isVisible }: LoadingOverlayProps) {
//   return (
//     <AnimatePresence>
//       {isVisible && (
//         <motion.div
//           className="absolute inset-0 z-50 bg-white bg-opacity-50 flex items-center justify-center"
//           initial={{ opacity: 0 }}
//           animate={{ opacity: 1 }}
//           exit={{ opacity: 0 }}
//         >
//           <Lottie
//             animationData={animationData}
//             loop
//             autoplay
//             className="h-50 w-50 object-contain"
//           />
//         </motion.div>
//       )}
//     </AnimatePresence>
//   );
// }

// components/LoadingOverlay.tsx

import { motion, AnimatePresence } from "framer-motion";
import Lottie from "lottie-react";
import videoLoader from "@/../../public/videocam.json";

interface LoadingOverlayProps {
  isVisible: boolean;
}

export default function LoadingOverlay({ isVisible }: LoadingOverlayProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="grow relative inset-0 z-10 flex items-center justify-center bg-black rounded-xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.1 }}
          exit={{ opacity: 0 }}
        >
          <div className="w-32 h-32">
            <Lottie animationData={videoLoader} loop autoplay />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
