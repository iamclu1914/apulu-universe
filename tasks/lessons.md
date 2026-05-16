# Lessons Learned

---

## ❌ DO NOT: Present web search results as credible without verifying the source

**What happened**: When asked whether NB2 prompts followed best practices, a web search returned results that appeared authoritative. The search summary was suspiciously clean (a signal of AI-generated/SEO content). One fetched source (dev.to/googleai) was cited as NB2 guidance without verifying that `googleai` on dev.to is an official Google account — it is not. The Google Cloud blog fetch failed entirely (returned page scaffolding, not article content), yet conclusions were still drawn.

**The mistake**: Presented unverified community blog content as authoritative best-practice guidance and used it to critique the existing implementation.

**The rule**:
1. When a web search summary is suspiciously well-formed, treat it as potentially AI-generated — fetch the actual URLs before drawing conclusions.
2. dev.to, Medium, Substack, etc. are community platforms — a username like "googleai" is NOT verified as the company.
3. If a fetch returns page scaffolding instead of article content, do NOT proceed as if you retrieved the content.
4. When uncertain about a third-party tool's official documentation, ask the user for the canonical source before making claims.
5. Flag source credibility issues to the user BEFORE presenting findings, not after.
