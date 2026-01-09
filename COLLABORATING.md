# Collaborating

This is a guide for us to work well as a team and not interfere with what we are each changing at any point in time.

I will explain every concept we need to know for collaborating well in detail, assuming audience is ignorant. If you already know that, **skip**.

I am doing it this way because I don't know how familiar we each are with git and GitHub collaboration, so just wanna make sure we're all on the same wavelength.

---

# Working on different branches
We are each working on different parts of the project. I am doing mostly backend, and Vivian and Eason are doing mostly frontend. They should not interfere with each other, but best practice is that each person works on a different branch, making commits there and pushing there before merging into the main/master branch.

I have created the branches for each of us. To see branches, go to the [GitHub repository](github.com/Albertlungu/CNLC) and underneath the title, you will see a label saying `4 Branches`. Once you click that, you can see all available branches.

When cloning a repository, it automatically puts you on the main branch. To switch to your branch:
```bash
git clone https://github.com/Albertlungu/CNLC.git # This clones the repository into the directory that your terminal currently is at
git checkout -t origin/<your-branch> # Put your branch name here
```
Once you make your first change, you must stage it, and make a meaningful commit message (try to use prefixes, which I have put for you in `./for_teammates`):
```bash
git add path/to/your/file # or git add . to add everything
git commit -m "PREFIX: Message goes here."
```
Then, if this is your first commit to this branch, push using:
```bash
git push -u origin <your-branch> # Again, branch name here
```
After that, you can simply do
```bash
git push
```

>[!NOTE] This only saves your edits to the branch. To bring everything into the main branch, see the next step.

---

# Merging
Once you're done your edits for the day or period of time, you update your branch with the latest main then open a Pull Request.

**1**. First, make sure you're on the correct branch with the `git checkout` command stated above.

**2**. Fetch the latest changes from main:
```bash
git fetch origin
```
> [!NOTE]
> This pulls all changes from the remote repo (from GitHub) into your local Git (so basically onto your local drive).
>
> This does NOT modify your working files, it just "tells" your Git that there have been other commits/changes made on main and what they are.

**3**. Merge main into your branch
```bash
git merge origin/main
```
This combines the changes and commits from the main branch with your branch's commits.

If any file was changed on both branches, Git will stop, and mark the **conflict**.

This conflict must first be **resolved manually**, then you stage and commit:
> [!NOTE]
> **For resolving conflicts**: They are normally flagged by something that looks like:
>
> `<<<<<<`
>
> `<conflict>`
>
> `>>>>>>`
>
> VS Code tries to make resolving these easier in their UI, but it can be quite annoying and difficult if you've never seen VS Code's format for displaying conflicts.
>
> A way to do this if you really don't understand anything: Just ask an AI. Do **not** auto-accept code. Always verify what they are doing in detail.
```bash
git add <resolved-files>
git commit -m "PREFIX: Commit message here"
```
Now, your branch contains all of your edits **plus** all the commits from main, and the commit history shows a merge commit.

**4**. Push your branch
```bash
git push
```
Or if Git gives some errors that look like:
```bash
To https://github.com/USERNAME/REPO.git
 ! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs to 'https://github.com/USERNAME/REPO.git'
hint: Updates were rejected because the remote contains work that you do not have locally.
hint: You may want to first integrate the remote changes (e.g., 'git pull ...') before pushing again.
hint: See the 'Note about fast-forwards' in 'git push --help' for details.
```
Then you should do what it says, and run:
```bash
git pull
```

Resolve conflicts if necessary. Then:
```bash
git push
```

---

# Pull Requests
If you've done everything right, if you go to GitHub, you will see a big notification right at the top of the page with a big fat green button saying something like: `Create Pull Request`.

Then, you fill out the fields the Pull Requests asks you to fill out, including a commit message and a short description, and you click the other big green button at the bottom of the page.

## Who will review these?
Uhhh probably I will cause I'm completely unemployed. So when you make a PR (Pull Request) just send a message to the GC on Insta and I'll try and review it ASAP. If there's something that needs further clarification, I'll dm you about it and we can discuss it as a team.