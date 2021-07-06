from django import forms
from django.db import models

from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.contrib.taggit import ClusterTaggableManager
from taggit.models import TaggedItemBase

from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index
from wagtail.snippets.models import register_snippet


@register_snippet
class NewsCategory(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("name"),
        ImageChooserPanel("icon"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "news categories"


class NewsIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [FieldPanel("intro", classname="full")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        newspages = self.get_children().live().order_by("-first_published_at")
        context["newspages"] = newspages
        return context


class NewsTagIndexPage(Page):
    def get_context(self, request):

        # Filter by tag
        tag = request.GET.get("tag")
        newspages = NewsPage.objects.filter(tags__name=tag)

        # Update template context
        context = super().get_context(request)
        context["newspages"] = newspages
        return context


class NewsPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "NewsPage", related_name="tagged_items", on_delete=models.CASCADE
    )


class NewsPage(Page):
    """
    Showing a news item
    """

    body = RichTextField(blank=True)
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    tags = ClusterTaggableManager(through=NewsPageTag, blank=True)
    categories = ParentalManyToManyField("news.NewsCategory", blank=True)
    feed_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.SearchField("date"),
    ]

    # Editor panels configuration

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel("tags"),
                FieldPanel("categories", widget=forms.CheckboxSelectMultiple),
            ],
            heading="News information",
        ),
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
        InlinePanel("related_links", label="Related Links"),
        InlinePanel("gallery_images", label="Gallery images"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        ImageChooserPanel("feed_image"),
    ]

    # master detail rules (parent / subpage)
    parent_page_types = ["news.NewsIndexPage"]
    subpage_types = []

    def main_image(self):
        gallery_item = self.gallery_images.first()
        if gallery_item:
            return gallery_item.image
        else:
            return None


class NewsPageRelatedLink(Orderable):
    """
    Related links for a news item
    """

    page = ParentalKey(NewsPage, on_delete=models.CASCADE, related_name="related_links")
    name = models.CharField(max_length=255)
    url = models.URLField()

    panels = [
        FieldPanel("name"),
        FieldPanel("url"),
    ]


class NewsPageGalleryImage(Orderable):
    page = ParentalKey(
        NewsPage, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        ImageChooserPanel("image"),
        FieldPanel("caption"),
    ]
