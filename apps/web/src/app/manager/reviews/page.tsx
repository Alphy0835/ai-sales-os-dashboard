import { Suspense } from "react";
import { ReviewHistoryView } from "@/components/ReviewHistory";

export default function ManagerReviewsPage() {
  return (
    <Suspense fallback={<div className="text-secondary">Загрузка…</div>}>
      <ReviewHistoryView />
    </Suspense>
  );
}
