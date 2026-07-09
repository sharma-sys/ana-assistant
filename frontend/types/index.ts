export interface NewsArticle {
  id: string | number;
  title: string;
  source: string;
  source_url: string;
  published_at: string;
  state: string;
  city: string;
  status: string;
  image_url?: string;
  references?: string;
  category?: string;
  credibility_score?: number;
  credibility_status?: string;
}

export interface AIResult {
  content: string;
  seo_title: string;
  meta_description: string;
  keywords: string;
  slug: string;
  category?: string;
}
