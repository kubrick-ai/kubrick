import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { SearchParams, SearchFormSchema } from "@/types";
import { z } from "zod";
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
    query_media_type: undefined,
    query_media_url: undefined,
    query_media_file: undefined,
    query_modality: ["visual-text" as const],
    search_scope: "clip" as const,
    search_modality: "all" as const,
    min_similarity: 0.2,
    page_limit: 10,
    filter: "",
  };

  const form = useForm<z.infer<typeof SearchFormSchema>>({
    resolver: zodResolver(SearchFormSchema),
    defaultValues,
  });

  const onSubmit = (values: z.infer<typeof SearchFormSchema>) => {
    const params: SearchParams = {
      query_text: values.query_text,
      query_media_type: values.query_media_type,
      query_media_url: values.query_media_url,
      query_media_file: values.query_media_file,
      query_modality: values.query_modality,
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
    setSearchParams({});
    form.reset({
      ...defaultValues,
    });
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        <div className="flex w-full max-w-sm items-center gap-1">
          <FormField
            control={form.control}
            name="query_text"
            render={({ field }) => (
              <FormItem className="flex-1">
                <FormControl>
                  <Input placeholder="Enter search query..." {...field} />
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <FormField
                control={form.control}
                name="query_media_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Media Type</FormLabel>
                    <Select
                      onValueChange={field.onChange}
                      value={field.value || ""}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select media type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
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
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Media File</FormLabel>
                    <FormControl>
                      <Input
                        type="file"
                        accept="image/*,video/*,audio/*"
                        onChange={(e) => field.onChange(e.target.files?.[0])}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="search_scope"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Scope</FormLabel>
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
                name="query_modality"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Query Modality</FormLabel>
                    <DropdownMenu>
                      <FormControl>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="outline"
                            className="justify-between w-42 "
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
                              field.onChange([...currentValues, "visual-text"]);
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

              <FormField
                control={form.control}
                name="search_modality"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Search Modality</FormLabel>
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
                    <FormLabel>Min Similarity: {field.value}</FormLabel>
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
                  <FormLabel>Advanced Filter (JSON)</FormLabel>
                  <FormControl>
                    <textarea
                      className="w-full p-2 border rounded-md"
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
