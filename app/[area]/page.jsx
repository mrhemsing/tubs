import '../styles.css';
import ReviewPage, { slugToArea, areaOrder, areaSlugs } from '../review';
import { notFound } from 'next/navigation';

export function generateStaticParams() {
  return areaOrder.map((area) => ({ area: areaSlugs[area] }));
}

export async function generateMetadata({ params }) {
  const { area: slug } = await params;
  const area = slugToArea[slug];
  return {
    title: area ? `${area} Aerial Review` : 'Tubs Aerial Review',
  };
}

export default async function AreaPage({ params }) {
  const { area: slug } = await params;
  const area = slugToArea[slug];
  if (!area) notFound();
  return <ReviewPage areaFilter={area} />;
}
