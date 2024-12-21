from django.contrib import admin
from mcqs.models import Subject,Unit,Chapter, Topic,MCQ,mcq_types,difficulties,TestSession,TestAnswer,Bookmark
# Register your models here.
from django import forms
# from .models import MCQ
# Register your models here.
# admin.site.register(MCQ)


class SubjectFilter(admin.SimpleListFilter):
    title = 'Subject'
    parameter_name = 'subject'

    def lookups(self, request, model_admin):
        subjects = Subject.objects.all()
        return [(subject.uid, subject.name) for subject in subjects]

    def queryset(self, request, queryset):
        if 'topic' in request.path:
            # Filtering logic for Topic view
            if self.value():
                return queryset.filter(chapter__unit__subject__uid=self.value())
        elif 'chapter' in request.path:
            # Filtering logic for Chapter view
            if self.value():
                return queryset.filter(unit__subject__uid=self.value())
        return queryset

class UnitFilter(admin.SimpleListFilter):
    title = 'Unit'
    parameter_name = 'unit'

    def lookups(self, request, model_admin):
        subject_uid = request.GET.get('subject')
        if subject_uid:
            units = Unit.objects.filter(subject__uid=subject_uid)
            return [(unit.uid, unit.name) for unit in units]
        return []

    def queryset(self, request, queryset):
        if 'topic' in request.path:
            if self.value():
                return queryset.filter(chapter__unit__uid=self.value())
            return queryset
        elif 'chapter' in request.path:
            if self.value():
                return queryset.filter(unit__uid=self.value())
            return queryset

class ChapterFilter(admin.SimpleListFilter):
    title = 'Chapter'
    parameter_name = 'chapter'

    def lookups(self, request, model_admin):
        unit_uid = request.GET.get('unit')
        if unit_uid:
            chapters = Chapter.objects.filter(unit__uid=unit_uid)
            return [(chapter.uid, chapter.name) for chapter in chapters]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(chapter__uid=self.value())
        return queryset
# class ChapterFilter(admin.SimpleListFilter):
#     title = 'Chapter'
#     parameter_name = 'chapter'

#     def lookups(self, request, model_admin):
#         unit_uid = request.GET.get('unit')
#         if unit_uid:
#             chapters = Chapter.objects.filter(unit__uid=unit_uid)
#             return [(chapter.uid, chapter.name) for chapter in chapters]
#         return []

#     def queryset(self, request, queryset):
#         if self.value():
#             return queryset.filter(chapter__uid=self.value())
#         return queryset



class MCQAdminForm(forms.ModelForm):
    class Meta:
        model = MCQ
        fields = '__all__'

    class Media:
        js = ('mcqs/js/dynamic_dropdowns.js',)  # Include your custom JavaScript file

class MCQAdmin(admin.ModelAdmin):
    form = MCQAdminForm





class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    search_fields = ('name', )
    ordering = ['created_at']


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1
    search_fields = ('name', )
    ordering = ['created_at']


class UnitInline(admin.TabularInline):
    
    model = Unit
    extra = 1
    search_fields = ('name', )
    
class SubjectAdmin(admin.ModelAdmin):
    inlines = [UnitInline]
    search_fields = ('name', )
    ordering = ['order']

class MCQAdmin(admin.ModelAdmin):
    search_fields = ('text', )

class UnitAdmin(admin.ModelAdmin):
    inlines = [ChapterInline]
    search_fields = ('name', )
    list_filter = ['subject']
    ordering = ['subject','order']


class ChapterAdmin(admin.ModelAdmin):
    inlines = [TopicInline]
    search_fields = ('name', )
    ordering = ['order']
    list_filter = [SubjectFilter, UnitFilter]

class MCQInline(admin.StackedInline):
    
    model = MCQ
    extra = 1
    search_fields = ('name', )  
    
class TopicAdmin(admin.ModelAdmin):
    inlines = [MCQInline]
    search_fields = ('name', )
    ordering = ['order']
    
    list_filter = [SubjectFilter, UnitFilter, ChapterFilter]

admin.site.register(Subject, SubjectAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(Chapter, ChapterAdmin)
admin.site.register(Topic,TopicAdmin)
admin.site.register(MCQ, MCQAdmin)
admin.site.register(mcq_types)
admin.site.register(difficulties)
admin.site.register(TestSession)
admin.site.register(TestAnswer)
admin.site.register(Bookmark)