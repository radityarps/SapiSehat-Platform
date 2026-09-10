import { ArticleEditorPage } from "@/src/features/agency/guides/article-editor-page";

export default async function EditGuideArticlePage({
	params,
}: {
	params: Promise<{ articleId: string }>;
}) {
	const { articleId } = await params;
	return <ArticleEditorPage mode="edit" articleId={articleId} />;
}
