export const PASSWORD_MIN_LENGTH = 12

export function passwordIssues(password: string): string[] {
  const issues: string[] = []
  if (password.length < PASSWORD_MIN_LENGTH) issues.push(`At least ${PASSWORD_MIN_LENGTH} characters`)
  if (!/[A-Z]/.test(password)) issues.push('One uppercase letter')
  if (!/[a-z]/.test(password)) issues.push('One lowercase letter')
  if (!/\d/.test(password)) issues.push('One digit')
  if (!/[^\w\s]/.test(password)) issues.push('One special character')
  return issues
}
