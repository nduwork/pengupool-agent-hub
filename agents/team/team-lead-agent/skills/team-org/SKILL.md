---
name: team-org
description: Use when you lead a PenguPool team and need to know who does what - choosing which member gets a part of the work, finding how to reach a member, noticing a part no member can do, a member whose work is finished, or a member with no clear role. Reads the roster and the team tree from context, routes work by role, and asks the owner to add or remove a member; it never changes the team, a role or an assignment itself.
triggers:
  - who should do
  - who owns
  - roster
  - add a member
  - remove a member
  - new lead
  - no one can
  - regroup
---

# Team org — know the team and route by role

## Read the team from your context

Your context gives you two views of the same team:

- **The roster:** every active member as "name — role", with its current assignment, and which
  member is the LEAD. The three roles are automatic: **LEAD** is the session at the root of the
  team tree, **BUILDER** is a member the owner added that has a repository behind it, and **HELPER** is
  an agent taken from the helper pool.
- **The tree:** your own parent and children, and how to reach each. The owner sets it by
  regrouping members on the map; helpers sit under the root session by default. You reach only your
  parent and children (and the other top-level members when you are at the top level). The LEAD is
  always the session at the tree's root, so leadership changes only when the owner regroups the
  tree on the map.

The roster says who can do a thing; the tree says how a message gets there. Read both before you
route anything. You cannot set roles or assignments; they change when the owner changes them.

## Route by role

1. Match each part of the work to the role whose words fit it best: a repository member for code
   in its repository, a helper for its skill (review, CI, research, …).
2. Prefer the member already working near that part; avoid giving two members the same files.
3. Find the path: if the member is your child, send it directly; otherwise relay through the
   child whose subtree holds it, or through your parent (skill `team-hub`).
4. When two roles fit equally, ask the owner rather than guess.

## When the team should change

Every change is a request the owner approves. Until it is approved, plan without it.

| Situation | Request |
| --- | --- |
| A part needs a repository or skill no member has | `pengupool team request add --skill <name>\|--repo <name> --assignment "<objective; done when>"` |
| A member's part is done and will not come back | `pengupool team request remove <member> --reason "<why>"` |
| The same far-apart pair keeps needing each other through long relays | Suggest the owner regroup them on the map |

Before you ask to remove a member, make sure what it finished and what is open is in its messages
to you, so the record has it, and that each open part has a new owner.

## Keep the team small and clear

- Fewer members with clear parts beat many with overlapping ones; a part with no owner is a gap,
  a part with two owners is a conflict.
- When a member's role does not say what it does, or its role and its assignment disagree, ask the
  owner one question about it. Do not invent a role.
- When the owner adds a member, send it, through the tree, its assignment and where the current
  status is.
