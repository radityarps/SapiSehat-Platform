import * as React from 'react';
import { cn } from '@/lib/utils';

export const Separator = React.forwardRef<HTMLHRElement, React.HTMLAttributes<HTMLHRElement>>(({ className, ...props }, ref) => (
  <hr ref={ref} className={cn('shrink-0 border-t border-border', className)} {...props} />
));
Separator.displayName = 'Separator';
