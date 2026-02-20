"use client";

import { useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SearchIcon, XIcon } from "lucide-react";
import type { UserListParams } from "@/types/user";
import { useTiers } from "@/hooks/useTiers";

interface UserFiltersProps {
  filters: UserListParams;
  onFilterChange: (filters: UserListParams) => void;
}

export function UserFilters({ filters, onFilterChange }: UserFiltersProps) {
  const { data: tiers } = useTiers();
  const [searchInput, setSearchInput] = useState(filters.search || "");

  const handleSearch = useCallback(() => {
    onFilterChange({ ...filters, search: searchInput || undefined, page: 1 });
  }, [filters, onFilterChange, searchInput]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") handleSearch();
    },
    [handleSearch]
  );

  const handleStatusChange = useCallback(
    (value: string) => {
      const is_active =
        value === "all" ? null : value === "active" ? true : false;
      onFilterChange({ ...filters, is_active, page: 1 });
    },
    [filters, onFilterChange]
  );

  const handleTierChange = useCallback(
    (value: string) => {
      onFilterChange({
        ...filters,
        user_class: value === "all" ? null : value,
        page: 1,
      });
    },
    [filters, onFilterChange]
  );

  const removeFilter = useCallback(
    (key: keyof UserListParams) => {
      const updated = { ...filters, [key]: key === "is_active" ? null : undefined, page: 1 };
      if (key === "search") setSearchInput("");
      onFilterChange(updated);
    },
    [filters, onFilterChange]
  );

  // Active filter chips
  const activeFilters: Array<{ key: keyof UserListParams; label: string }> = [];
  if (filters.search) activeFilters.push({ key: "search", label: `Search: "${filters.search}"` });
  if (filters.is_active !== null && filters.is_active !== undefined)
    activeFilters.push({
      key: "is_active",
      label: `Status: ${filters.is_active ? "Active" : "Inactive"}`,
    });
  if (filters.user_class)
    activeFilters.push({ key: "user_class", label: `Tier: ${filters.user_class}` });

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-sm">
          <SearchIcon className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search by name or email..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="pl-9"
          />
        </div>

        {/* Status filter */}
        <Select
          value={
            filters.is_active === null || filters.is_active === undefined
              ? "all"
              : filters.is_active
              ? "active"
              : "inactive"
          }
          onValueChange={handleStatusChange}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>

        {/* Tier filter */}
        <Select
          value={filters.user_class || "all"}
          onValueChange={handleTierChange}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Tier" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Tiers</SelectItem>
            {tiers?.map((tier) => (
              <SelectItem key={tier.name} value={tier.name}>
                {tier.display_name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Button variant="outline" size="sm" onClick={handleSearch}>
          <SearchIcon className="mr-1.5 size-4" />
          Search
        </Button>
      </div>

      {/* Active filter chips */}
      {activeFilters.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Active filters:</span>
          {activeFilters.map((f) => (
            <Badge
              key={f.key}
              variant="secondary"
              className="gap-1 pr-1 cursor-pointer"
              onClick={() => removeFilter(f.key)}
            >
              {f.label}
              <XIcon className="size-3" />
            </Badge>
          ))}
          {activeFilters.length > 1 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-xs"
              onClick={() => {
                setSearchInput("");
                onFilterChange({ page: 1 });
              }}
            >
              Clear all
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
