"use client";

import { useState } from "react";
import * as Collapsible from "@radix-ui/react-collapsible";
import { ChevronDown, ChevronUp, AlertCircle } from "lucide-react";
import { DetailedError } from "@/types";

interface ErrorDisplayProps {
  error: DetailedError
  className?: string;
}

const ErrorDisplay = ({ error, className = ''}: ErrorDisplayProps) => {
  const [showDetails, setShowDetails] = useState(false);

    const isDetailedError = (err: DetailedError | Error): err is DetailedError => {
    return 'statusCode' in err || 'responseData' in err || 'isNetworkError' in err;
  };

    const detailedError = isDetailedError(error) ? error : null;

    const safeStringify = (value: unknown): string => {
      try {
        if (typeof value === 'string') {
          return value;
        }
        return JSON.stringify(value, null, 2);
      }  catch {
        return String(value);
      }
    };

  const ErrorToString = (value: unknown): string => {
    try {
      if (value instanceof Error) {
        return value.message;
      }
      return String(value);
    } catch {
      return 'Unable to display error details';
    }
  };

  const getErrorMessage = () => {
    if (detailedError?.isNetworkError) {
      return "Network connection error.";
    }
    
    if (detailedError?.statusCode) {
      if (detailedError.statusCode === 400) {
          return "Invalid request.";
      } else if (detailedError.statusCode === 422) {
          return "Media Processing error";
      } else if (detailedError.statusCode === 503) {
        return "Database Error"
      } else if (detailedError.statusCode < 500) {
        return "Request Error"
      } else {
        return detailedError.message || "An unexpected error occurred."
      }
    }
    return error.message || "An unexpected error occurred.";
  }
  
  const getServerMessage = () => {
    if (detailedError?.responseData) {
      if (typeof detailedError.responseData === 'string') {
        return detailedError.responseData;
      }
      
      if (typeof detailedError.responseData === 'object' && detailedError.responseData !== null) {
        const data = detailedError.responseData as Record<string, unknown>;
        
        if (typeof data.message === 'string') {
          return data.message;
        }
        if (typeof data.error === 'string') {
          return data.error;
        }
        if (typeof data.detail === 'string') {
          return data.detail;
        }
      }
    }
    return null;
  };

  return (
    <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <AlertCircle className="h-5 w-5 text-red-400" />
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-red-800">
            Error
          </h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{getErrorMessage()}</p>
          </div>

          {(detailedError?.statusCode || getServerMessage()) && (
            <div className="mt-3 text-sm text-red-600">
              {detailedError?.statusCode && (
                <p><strong>Status:</strong> {detailedError.statusCode} {detailedError.statusText}</p>
              )}
              {getServerMessage() && (
                <p><strong>Server Message:</strong> {getServerMessage()}</p>
              )}
            </div>
          )}

          {detailedError && (
            <Collapsible.Root open={showDetails} onOpenChange={setShowDetails} className="mt-4">
              <Collapsible.Trigger asChild>
                <button className="flex items-center text-sm text-red-600 hover:text-red-800 focus:outline-none focus:underline">
                  {showDetails ? (
                    <>
                      <ChevronUp className="h-4 w-4 mr-1" />
                      Hide technical details
                    </>
                  ) : (
                    <>
                      <ChevronDown className="h-4 w-4 mr-1" />
                      Show technical details
                    </>
                  )}
                </button>
              </Collapsible.Trigger>

              <Collapsible.Content className="mt-3 p-3 bg-red-100 rounded border text-xs text-red-800 font-mono">
                <div className="space-y-2">
                  {detailedError.requestUrl && (
                    <div>
                      <strong>Request:</strong> {detailedError.requestMethod || 'GET'} {detailedError.requestUrl}
                    </div>
                  )}
                  {detailedError.statusCode && (
                    <div>
                      <strong>Status Code:</strong> {detailedError.statusCode}
                    </div>
                  )}
                  {detailedError.responseData !== undefined && (
                    <div>
                      <strong>Response Data:</strong>
                      <pre className="mt-1 whitespace-pre-wrap break-all">
                        {safeStringify(detailedError.responseData)}
                      </pre>
                    </div>
                  )}
                  {detailedError.originalError !== undefined && (
                    <div>
                      <strong>Original Error:</strong>
                      <pre className="mt-1 whitespace-pre-wrap break-all">
                        {ErrorToString(detailedError.originalError)}
                      </pre>
                    </div>
                  )}
                </div>
              </Collapsible.Content>
            </Collapsible.Root>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay;