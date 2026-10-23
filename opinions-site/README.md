# Opinions site

A single-page site (`index.html`, no build step) with opinions grouped into categories and subcategories. Every opinion has a short list of arguments and a reply field.

## Editing the content

Open `index.html` and edit the `SITE_CONTENT` list in the script. Add an object to a subcategory's `opinions` to publish a new one. Keep each opinion `id` stable once it is live, because replies are stored under it.

## Where replies are saved

By default replies are saved in the visitor's own browser (`localStorage`), so only that visitor sees them. To show every reply to every visitor you need a small database. The site supports a Firebase Realtime Database with no SDK and no build step:

1. Create a project at the Firebase console and add a **Realtime Database**.
2. Paste these rules in the database's **Rules** tab. They let anyone read and add a reply (up to 1000 characters) but nobody edit or delete one:

   ```json
   {
     "rules": {
       "replies": {
         ".read": true,
         "$opinionId": {
           "$replyId": {
             ".write": "!data.exists()",
             ".validate": "newData.hasChildren(['text', 'createdAt']) && newData.child('text').isString() && newData.child('text').val().length <= 1000 && newData.child('createdAt').isNumber()"
           }
         }
       }
     }
   }
   ```

3. Copy the database URL (it looks like `https://<name>-default-rtdb.<region>.firebasedatabase.app`) into `REPLIES_DATABASE_URL` at the top of the script in `index.html`.

Anyone can still post anonymously, so expect some spam. Delete unwanted replies from the Firebase console.

## Hosting

It is one static file, so any static host works (GitHub Pages, Netlify, Cloudflare Pages, or just opening the file).
