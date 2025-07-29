import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SearchParams, SearchFormData, SearchFormDataSchema } from "@/types";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuCheckboxItem,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useEffect } from "react";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface SearchFormParams {
  setSearchParams: (params: SearchParams) => void;
  isOptionsOpen: boolean;
  setIsOptionsOpen: (open: boolean) => void;
}

const SearchForm = ({
  setSearchParams,
  isOptionsOpen,
  setIsOptionsOpen,
}: SearchFormParams) => {
  const defaultValues = {
    query_text: "",
    query_type: "text" as const,
    query_media_url: undefined,
    query_media_file: undefined,
    query_modality: ["visual-text" as const],
    search_scope: "clip" as const,
    search_modality: "all" as const,
    min_similarity: 0.2,
    page_limit: 10,
    filter: "",
  };

  const form = useForm<SearchFormData>({
    resolver: zodResolver(SearchFormDataSchema),
    defaultValues,
  });

  const queryType = form.watch("query_type");

  useEffect(() => {
    if (queryType !== "text") {
      form.setValue("query_media_file", undefined);
      if (queryType !== "video") {
        form.setValue("query_modality", ["visual-text"]);
      }
    }
  }, [queryType, form]);

  const onSubmit = (values: SearchFormData) => {
    const params: SearchParams = {
      query_text: values.query_text,
      query_type: values.query_type,
      query_media_url: values.query_media_url,
      query_media_file: values.query_media_file,
      query_modality: JSON.stringify(values.query_modality),
      min_similarity: values.min_similarity,
      page_limit: values.page_limit,
      filter: "{}",
    };

    try {
      const filter = {
        scope: values.search_scope === "all" ? undefined : values.search_scope,
        modality:
          values.search_modality === "all" ? undefined : values.search_modality,
        ...(values.filter ? JSON.parse(values.filter) : {}),
      };
      params.filter = JSON.stringify(filter);
    } catch {
      console.error("Invalid JSON in filter field");
      const filter = {
        scope: values.search_scope === "all" ? undefined : values.search_scope,
        modality:
          values.search_modality === "all" ? undefined : values.search_modality,
      };
      params.filter = JSON.stringify(filter);
    }

    setSearchParams(params);
  };

  const reset = () => {
    setSearchParams({
      query_type: "text",
    });
    form.reset({
      ...defaultValues,
    });
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div className="flex w-full max-w-md items-center gap-4">
          <FormField
            control={form.control}
            name="query_text"
            render={({ field }) => (
              <FormItem className="flex-1">
                <FormControl>
                  <Input
                    className="min-w-90"
                    placeholder="Enter search query..."
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button type="submit">Search</Button>
        </div>

        <Collapsible open={isOptionsOpen} onOpenChange={setIsOptionsOpen}>
          <CollapsibleTrigger asChild>
            <Button variant="outline" className="flex items-center gap-2">
              {isOptionsOpen ? (
                <ChevronDown size={16} />
              ) : (
                <ChevronRight size={16} />
              )}
              Options
            </Button>
          </CollapsibleTrigger>

          <CollapsibleContent className="space-y-4 pt-4">
            <div className="grid grid-cols-1 md:grid-cols-[1fr_3fr_3fr_3fr] gap-4">
              <FormField
                control={form.control}
                name="query_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Query Type</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value || ""}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select query type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="text">Text</SelectItem>
                        <SelectItem value="image">Image</SelectItem>
                        <SelectItem value="video">Video</SelectItem>
                        <SelectItem value="audio">Audio</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="query_media_file"
                render={({ field }) => {
                  const getAcceptType = () => {
                    switch (queryType) {
                      case "image":
                        return "image/*";
                      case "video":
                        return "video/*";
                      case "audio":
                        return "audio/*";
                      default:
                        return "image/*,video/*,audio/*";
                    }
                  };

                  return (
                    <FormItem>
                      <FormLabel>Media File</FormLabel>
                      <FormControl>
                        <Input
                          type="file"
                          accept={getAcceptType()}
                          onChange={(e) => field.onChange(e.target.files?.[0])}
                          disabled={queryType === "text"}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  );
                }}
              />

              <FormField
                control={form.control}
                name="query_media_url"
                render={({ field }) => (
                  <FormItem className="flex-1">
                    <FormLabel>Media Url</FormLabel>
                    <FormControl>
                      <Input
                        className="min-w-40"
                        placeholder="Enter media url..."
                        {...field}
                        disabled={queryType === "text"}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {queryType === "video" && (
                <FormField
                  control={form.control}
                  name="query_modality"
                  render={({ field }) => (
                    <FormItem>
                      <TooltipProvider>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <FormLabel>Query Modality</FormLabel>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p>
                              Select which embedding modality of your query
                              video to search with
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>

                      <DropdownMenu>
                        <FormControl>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="outline"
                              className="justify-between w-42 "
                              disabled={queryType !== "video"}
                            >
                              {field.value && field.value.length > 0
                                ? field.value.join(", ")
                                : "Select Modality"}
                              <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                            </Button>
                          </DropdownMenuTrigger>
                        </FormControl>
                        <DropdownMenuContent>
                          <DropdownMenuLabel>Select</DropdownMenuLabel>
                          <DropdownMenuSeparator />
                          <DropdownMenuCheckboxItem
                            checked={field.value?.includes("visual-text")}
                            onCheckedChange={(checked) => {
                              const currentValues = field.value || [];
                              if (checked) {
                                field.onChange([
                                  ...currentValues,
                                  "visual-text",
                                ]);
                              } else {
                                field.onChange(
                                  currentValues.filter(
                                    (v) => v !== "visual-text",
                                  ),
                                );
                              }
                            }}
                          >
                            Visual-Text
                          </DropdownMenuCheckboxItem>
                          <DropdownMenuCheckboxItem
                            checked={field.value?.includes("audio")}
                            onCheckedChange={(checked) => {
                              const currentValues = field.value || [];
                              if (checked) {
                                field.onChange([...currentValues, "audio"]);
                              } else {
                                field.onChange(
                                  currentValues.filter((v) => v !== "audio"),
                                );
                              }
                            }}
                          >
                            Audio
                          </DropdownMenuCheckboxItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-[1fr_4fr_2fr] gap-4">
              <FormField
                control={form.control}
                name="search_scope"
                render={({ field }) => (
                  <FormItem>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <FormLabel>Scope</FormLabel>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>Filter search results by their embedding scope.</p>
                          <p>
                            - `clip` will search embeddings of video segments,
                          </p>
                          <p>
                            - `video` will search embeddings of entire videos.
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value || ""}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select scope" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value="video">Video</SelectItem>
                        <SelectItem value="clip">Clip</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="search_modality"
                render={({ field }) => (
                  <FormItem>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <FormLabel>Search Modality</FormLabel>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>
                            Filter search results by their embedding modality
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value || ""}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select modality to search" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value="visual-text">Visual-Text</SelectItem>
                        <SelectItem value="audio">Audio</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="min_similarity"
                render={({ field }) => (
                  <FormItem>
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <FormLabel>Min Similarity: {field.value}</FormLabel>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>
                            Threshold for minimum Cosine Similarity of a search
                            result
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                    <FormControl>
                      <Slider
                        min={0}
                        max={1}
                        step={0.01}
                        value={[field.value ?? 0.5]}
                        onValueChange={(value) => field.onChange(value[0])}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="filter"
              render={({ field }) => (
                <FormItem>
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <FormLabel>Advanced Filter (JSON)</FormLabel>
                      </TooltipTrigger>
                      <TooltipContent>
                        <p>Filter on metadata using a JSON</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                  <FormControl>
                    <textarea
                      className="w-md p-2 border rounded-md"
                      rows={3}
                      placeholder='{"key": "value"}'
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="button" variant="outline" onClick={reset}>
              Reset
            </Button>
          </CollapsibleContent>
        </Collapsible>
      </form>
    </Form>
  );
};

export default SearchForm;

