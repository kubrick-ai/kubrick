"use client";

import { BookOpen, SquareTerminal } from "lucide-react";
import AppSidebarMain from "@/components/AppSidebarMain";
import AppSidebarHeader from "@/components/AppSidebarHeader";
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar";

// This is sample data.
const data = {
  navMain: [
    {
      title: "Playground",
      icon: SquareTerminal,
      isActive: true,
      items: [
        {
          title: "Search",
          url: "/search",
        },
        {
          title: "Library",
          url: "/library",
        },
        {
          title: "Embed",
          url: "/embed",
        },
        {
          title: "Embedding Tasks",
          url: "/embedding_tasks",
        },
      ],
    },
    {
      title: "Documentation",
      icon: BookOpen,
      items: [
        {
          title: "Get Started",
          url: "http://kubrick-ai.com/guides/quick-start",
        },
        {
          title: "API Reference",
          url: "http://kubrick-ai.com/api",
        },
      ],
    },
  ],
};

const AppSidebar = ({ ...props }: React.ComponentProps<typeof Sidebar>) => {
  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <AppSidebarHeader />
      </SidebarHeader>
      <SidebarContent>
        <AppSidebarMain items={data.navMain} />
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
};

export default AppSidebar;
