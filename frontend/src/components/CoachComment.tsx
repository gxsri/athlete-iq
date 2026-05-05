import React from 'react';
import { Star, Trash2, Edit2, User, CheckCheck, Eye } from 'lucide-react';
import type { CoachComment as CoachCommentType } from '../services/api';

interface CoachCommentProps {
  comment: CoachCommentType & { is_read?: boolean; read_by_athlete?: boolean; read_at?: string };
  isCoachMode?: boolean;
  onEdit?: (comment: CoachCommentType) => void;
  onDelete?: (id: string) => void;
  onMarkRead?: (id: string) => void;
}

export function CoachComment({ comment, isCoachMode, onEdit, onDelete, onMarkRead }: CoachCommentProps) {
  const isRead = comment.read_by_athlete || comment.is_read;

  return (
    <div
      className={`p-4 rounded-2xl border transition-all duration-200 ${
        !isRead ? 'bg-[#e8f2ff]/40 border-[#007aff]/20' : 'bg-white border-[#e5e5ea]'
      }`}
      onClick={() => !isRead && onMarkRead?.(comment.id)}
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[#007aff] to-[#5856d6] flex items-center justify-center">
            <User className="w-3.5 h-3.5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[13px] font-semibold text-[#1d1d1f]">{comment.created_by_name || '教练'}</span>
              {isCoachMode && (
                <span className={`read-dot ${isRead ? 'read-dot-read' : 'read-dot-unread'}`} title={isRead ? '已读' : '未读'} />
              )}
            </div>
            <span className="text-[11px] text-[#aeaeb2]">{comment.created_at}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Read status for athlete view */}
          {!isCoachMode && !isRead && (
            <button
              onClick={(e) => { e.stopPropagation(); onMarkRead?.(comment.id); }}
              className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-[#007aff]/10 text-[#007aff] text-[11px] font-medium hover:bg-[#007aff]/20 transition-colors"
            >
              <Eye className="w-3 h-3" /> 标为已读
            </button>
          )}
          {!isCoachMode && isRead && (
            <span className="flex items-center gap-1 text-[11px] text-[#34c759]">
              <CheckCheck className="w-3 h-3" /> 已读
            </span>
          )}

          {/* Rating stars */}
          <div className="flex items-center gap-0.5">
            {Array.from({ length: 5 }, (_, i) => (
              <Star
                key={i}
                className={`w-3.5 h-3.5 ${i < Math.round((comment.rating || 0) / 2)
                  ? 'text-[#ff9500] fill-[#ff9500]'
                  : 'text-[#e5e5ea]'}`}
              />
            ))}
          </div>

          {/* Coach mode controls */}
          {isCoachMode && (
            <div className="flex items-center gap-0.5" onClick={e => e.stopPropagation()}>
              <button onClick={() => onEdit?.(comment)} className="btn-icon">
                <Edit2 className="w-3.5 h-3.5" />
              </button>
              <button onClick={() => onDelete?.(comment.id)} className="btn-icon hover:bg-[#ffeaea] hover:text-[#ff3b30]">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      <p className="text-[14px] text-[#3a3a3c] leading-relaxed">{comment.comment_text}</p>
    </div>
  );
}
