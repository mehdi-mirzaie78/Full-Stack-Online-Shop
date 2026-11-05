"use client";
import { Tabs as TabsPrimitive } from "@base-ui/react/tabs";
import { cn } from "@/lib/utils";

type ClassName = { className?: string };
const Tabs = TabsPrimitive.Root;

function TabsList({ className, ...props }: Omit<TabsPrimitive.List.Props, "className"> & ClassName) {
  return <TabsPrimitive.List data-slot="tabs-list" className={cn("inline-flex max-w-full items-center gap-1 rounded-lg bg-muted p-1 text-muted-foreground", className)} {...props} />;
}

function TabsTrigger({ className, ...props }: Omit<TabsPrimitive.Tab.Props, "className"> & ClassName) {
  return <TabsPrimitive.Tab data-slot="tabs-trigger" className={cn("inline-flex min-h-8 items-center justify-center whitespace-nowrap rounded-md px-3 py-1.5 text-sm font-medium outline-none data-[active]:bg-background data-[active]:text-foreground data-[active]:shadow-sm focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50", className)} {...props} />;
}

function TabsContent({ className, ...props }: Omit<TabsPrimitive.Panel.Props, "className"> & ClassName) {
  return <TabsPrimitive.Panel data-slot="tabs-content" className={cn("mt-5 outline-none focus-visible:ring-2 focus-visible:ring-ring", className)} {...props} />;
}

export { Tabs, TabsList, TabsTrigger, TabsContent };
