import React from 'react';
import Image from 'next/image';
import { NewsArticle } from '../types';
import styles from './NewsListCard.module.css';

interface NewsListCardProps {
  article: NewsArticle;
  onGenerateAI: (id: string | number) => void;
  isGenerating: boolean;
}

export default function NewsListCard({ article, onGenerateAI, isGenerating }: NewsListCardProps) {
  const publishedDate = new Date(article.published_at + 'Z');
  
  const timeString = publishedDate.toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Kolkata'
  });

  return (
    <div className={styles.card}>
      <div className={styles.imageContainer}>
        <Image 
          src={article.image_url || '/default-news.png'} 
          alt={article.title} 
          className={styles.image}
          fill
          unoptimized
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = '/default-news.png';
            target.srcset = '';
          }}
        />
      </div>
      
      <div className={styles.content}>
        <div className={styles.header}>
          <span className={styles.source}>{article.source}</span>
          <span className={styles.time}>{timeString}</span>
        </div>
        
        <h3 className={styles.title} title={article.title}>
          {article.title}
        </h3>
        
        <div className={styles.location}>
          {article.state && article.state !== 'All' && <span className={styles.tag}>{article.state}</span>}
          {article.category && <span className={styles.tag}>{article.category}</span>}
        </div>
        
        <div className={styles.actions}>
          <a href={article.source_url} target="_blank" rel="noopener noreferrer" className={styles.linkButton}>
            Read Original
          </a>
          <button 
            className={`${styles.aiButton} ${isGenerating ? styles.loading : ''}`}
            onClick={() => onGenerateAI(article.id)}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : article.status === 'processed' ? 'View AI Data' : 'Generate AI'}
          </button>
        </div>
      </div>
    </div>
  );
}
