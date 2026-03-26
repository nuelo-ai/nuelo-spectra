"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import type { CreditPackage } from "@/hooks/useCreditPackages";

interface CreditPackageCardProps {
  pkg: CreditPackage;
}

export function CreditPackageCard({ pkg }: CreditPackageCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleBuy = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.post("/credits/purchase", { package_id: pkg.id });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data?.detail?.detail || "Failed to create checkout");
      }
      const { checkout_url } = await res.json();
      window.location.href = checkout_url;
      return; // navigating away
    } catch (err: any) {
      toast.error(err.message || "Something went wrong. Please try again.");
      setIsLoading(false);
    }
  };

  return (
    <Card className="text-center">
      <CardContent className="pt-4 pb-4 space-y-2">
        <p className="text-lg font-semibold">{pkg.credit_amount} credits</p>
        <p className="text-sm text-muted-foreground">{pkg.price_display}</p>
        <Button size="sm" variant="outline" className="w-full" onClick={handleBuy} disabled={isLoading}>
          {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Buy Credits"}
        </Button>
      </CardContent>
    </Card>
  );
}
