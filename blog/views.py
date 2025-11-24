from django.shortcuts import render
from .models import BlogPost, Comment
from django.shortcuts import render, get_object_or_404, redirect
from shop.models import Category
from django.core.paginator import Paginator
from django.db.models import Q
from .form import CommentForm

# Create your views here.

def blog(request):
    blogs = BlogPost.objects.defer("seo_title", "canonical", "content", "modified_date").all().order_by("-date_created")
    categories = Category.objects.defer("content", "seo_title", "meta").all()
    paginator = Paginator(blogs, 2)
    page_number = request.GET.get("page")
    page_object = paginator.get_page(page_number)
    return render(request, "blog.html", {"blogs":blogs, "categories":categories, "page_obj":page_object})

def blog_details(request, slug: str):
    blog = get_object_or_404(BlogPost, slug=slug)
    comments = Comment.objects.filter(blog=blog, approved=True)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.save()
    else:
        form = CommentForm()    
    
    categories = Category.objects.all()
    count = comments.count()
    return render(request, "blog-details.html", {"blog":blog, "comments":comments, "count":count, "categories":categories, "form":form})

def blog_search(request):
    categories = Category.objects.defer("content", "seo_title", "meta").all()
    search_term = request.GET.get("q", "").strip()
    blogs = BlogPost.objects.filter(Q(title__icontains=search_term) | Q(content__icontains=search_term)).order_by("-date_created")

    return render(request, "search-blog.html", {"blogs":blogs, "categories":categories})

