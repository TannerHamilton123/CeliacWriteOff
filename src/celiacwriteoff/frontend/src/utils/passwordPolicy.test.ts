import { describe, expect, it } from 'vitest'
import { passwordIssues } from './passwordPolicy'

// This is the gentlest possible first test: passwordIssues is a pure
// function (string in, string array out), so there's no rendering, no
// providers, no mocking -- just calling it and checking the result.
//
// More cases to add here as a learning exercise (see the plan for the full
// list): the exactly-11-vs-12-character boundary, a password missing only
// one rule at a time, and an edge case for the special-character check.

describe('passwordIssues', () => {
  it('flags every rule for an empty password', () => {
    const issues = passwordIssues('')
    expect(issues).toEqual([
      'At least 12 characters',
      'One uppercase letter',
      'One lowercase letter',
      'One digit',
      'One special character',
    ])
  })

  it('returns no issues for a password meeting every rule', () => {
    expect(passwordIssues('Str0ng!Passw0rd')).toEqual([])
  })
})
