import { NewsArticle, AIResult } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || 'ana_secure_dev_key_2026';

/**
 * Fetch with automatic retry — handles Render.com cold starts (30-60s spin-up).
 * Retries up to `maxRetries` times on network errors or 5xx responses.
 */
async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  maxRetries = 3,
  timeoutMs = 30000
): Promise<Response> {
  const mergedOptions: RequestInit = {
    cache: 'no-store', // Prevent aggressive Next.js caching
    ...options,
  };
  let lastError: Error = new Error('Unknown error');
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, { ...mergedOptions, signal: controller.signal });
      clearTimeout(timer);
      // Retry on 5xx server errors (e.g., Render waking up)
      if (response.status >= 500 && attempt < maxRetries) {
        await new Promise(r => setTimeout(r, 2000 * attempt));
        continue;
      }
      return response;
    } catch (err) {
      clearTimeout(timer);
      lastError = err instanceof Error ? err : new Error(String(err));
      if (attempt < maxRetries) {
        await new Promise(r => setTimeout(r, 2000 * attempt));
      }
    }
  }
  throw lastError;
}

/**
 * Fetch news articles from the FastAPI backend.
 */
export async function fetchNews(
  search: string = '',
  state: string = 'All',
  city: string = 'All',
  category: string = 'All',
  source: string = 'All',
  page: number = 1,
  limit: number = 20
): Promise<{ articles: NewsArticle[], totalPages: number }> {
  try {
    // Construct query parameters
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (state !== 'All') params.append('state', state);
    if (city !== 'All') params.append('district', city);
    if (category !== 'All') params.append('category', category);
    if (source !== 'All') params.append('source', source);
    params.append('page', page.toString());
    params.append('limit', limit.toString());

    const queryString = params.toString();
    const url = `${API_BASE_URL}/news/${queryString ? `?${queryString}` : ''}`;

    const response = await fetchWithRetry(url, {
      headers: {
        'X-API-Key': API_KEY,
      },
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch news: ${response.statusText}`);
    }

    const data = await response.json();
    
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const articles = data.items.map((item: any) => {
      // Fallback if source_name is missing for some reason
      let sourceName = item.source_name;
      if (!sourceName && item.source_url) {
        try {
          const urlObj = new URL(item.source_url);
          sourceName = urlObj.hostname.replace('www.', '');
        } catch {
          sourceName = 'Unknown Source';
        }
      }

      return {
        id: item.id,
        title: item.title,
        source: sourceName || 'Unknown Source',
        source_url: item.source_url || '#',
        published_at: item.published_at,
        state: item.state,
        city: item.district,
        status: item.status,
        image_url: item.image_url,
        references: item.references,
        category: item.category,
        credibility_score: item.credibility_score,
        credibility_status: item.credibility_status,
      };
    });

    return { articles, totalPages: data.pages || 1 };
  } catch (error) {
    console.error("API Error (fetchNews):", error);
    throw error;
  }
}

/**
 * Call the AI generation endpoint.
 */
export async function generateAIContent(articleId: string | number): Promise<AIResult> {
  try {
    const url = `${API_BASE_URL}/rewrite/generate`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
      body: JSON.stringify({ article_id: Number(articleId) }),
    });

    if (!response.ok) {
      let errorMsg = response.statusText;
      try {
        const errorData = await response.json();
        if (errorData && errorData.detail) errorMsg = errorData.detail;
      } catch {}
      throw new Error(errorMsg);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("API Error (generateAIContent):", error);
    throw error;
  }
}

/**
 * Trigger manual RSS fetch.
 */
export async function triggerRSSFetch(): Promise<{ status: string, new_articles_count: number }> {
  try {
    const url = `${API_BASE_URL}/news/fetch`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to trigger RSS fetch: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("API Error (triggerRSSFetch):", error);
    throw error;
  }
}

/**
 * Fetch active news sources.
 */
export async function fetchActiveSources(): Promise<{id: number, name: string}[]> {
  try {
    const url = `${API_BASE_URL}/sources`;
    const response = await fetchWithRetry(url, {
      headers: {
        'X-API-Key': API_KEY,
      }
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch sources: ${response.statusText}`);
    }
    const data = await response.json();
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return data.filter((s: any) => s.is_active).map((s: any) => ({ id: s.id, name: s.name }));
  } catch (error) {
    console.error("API Error (fetchActiveSources):", error);
    return [];
  }
}

/**
 * Fetch real states and districts from active news sources in the DB.
 */
export async function fetchFilters(): Promise<{ states: string[], districts: Record<string, string[]> }> {
  try {
    const url = `${API_BASE_URL}/sources/filters`;
    const response = await fetchWithRetry(url, {
      headers: { 'X-API-Key': API_KEY },
    });
    if (!response.ok) {
      throw new Error(`Failed to fetch filters: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("API Error (fetchFilters):", error);
    // Fallback: at least show All
    return { states: ['All'], districts: { All: ['All'] } };
  }
}

/**
 * Fetch exactly 1 latest article per active channel for the top grid.
 */
export async function fetchTopGridNews(
  search: string = '',
  state: string = 'All',
  city: string = 'All',
  category: string = 'All'
): Promise<NewsArticle[]> {
  try {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (state !== 'All') params.append('state', state);
    if (city !== 'All') params.append('district', city);
    if (category !== 'All') params.append('category', category);

    const queryString = params.toString();
    const url = `${API_BASE_URL}/news/top-grid${queryString ? `?${queryString}` : ''}`;
    
    const response = await fetchWithRetry(url, {
      headers: { 'X-API-Key': API_KEY },
    }, 3, 45000);
    if (!response.ok) {
      throw new Error(`Failed to fetch top grid news: ${response.statusText}`);
    }
    const data = await response.json();
    
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return data.map((item: any) => {
      let sourceName = item.source_name;
      if (!sourceName && item.source_url) {
        try {
          const urlObj = new URL(item.source_url);
          sourceName = urlObj.hostname.replace('www.', '');
        } catch {
          sourceName = 'Unknown Source';
        }
      }

      return {
        id: item.id,
        title: item.title,
        source: sourceName || 'Unknown Source',
        source_url: item.source_url || '#',
        published_at: item.published_at,
        state: item.state,
        city: item.district,
        status: item.status,
        image_url: item.image_url,
        references: item.references,
        category: item.category,
        credibility_score: item.credibility_score,
        credibility_status: item.credibility_status,
      };
    });
  } catch (error) {
    console.error("API Error (fetchTopGridNews):", error);
    return [];
  }
}

/**
 * Fetch latest 5 articles per source for Pramukh Samachar.
 */
export async function fetchPramukhSamachar(
  search: string = '',
  state: string = 'All',
  city: string = 'All',
  category: string = 'All'
): Promise<Record<string, NewsArticle[]>> {
  try {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (state !== 'All') params.append('state', state);
    if (city !== 'All') params.append('district', city);
    if (category !== 'All') params.append('category', category);

    const queryString = params.toString();
    const url = `${API_BASE_URL}/news/pramukh-samachar${queryString ? `?${queryString}` : ''}`;
    
    const response = await fetchWithRetry(url, {
      headers: { 'X-API-Key': API_KEY },
    }, 3, 45000);
    if (!response.ok) {
      throw new Error(`Failed to fetch pramukh samachar: ${response.statusText}`);
    }
    const data = await response.json();
    
    const grouped: Record<string, NewsArticle[]> = {};
    for (const source in data) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      grouped[source] = data[source].map((item: any) => ({
        id: item.id,
        title: item.title,
        source: item.source_name || source || 'Unknown Source',
        source_url: item.source_url || '#',
        published_at: item.published_at,
        state: item.state,
        city: item.district,
        status: item.status,
        image_url: item.image_url,
        references: item.references,
        category: item.category,
      }));
    }
    return grouped;
  } catch (error) {
    console.error("API Error (fetchPramukhSamachar):", error);
    return {};
  }
}

// force reload for nextjs watcher
